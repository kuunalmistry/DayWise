import os
import tempfile
import unittest
from datetime import date
from io import BytesIO
from unittest.mock import Mock, patch

import app as daywise
from werkzeug.security import check_password_hash, generate_password_hash


class DayWiseAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.upload_dir = os.path.join(cls.temp_dir.name, "uploads")
        os.makedirs(cls.upload_dir)
        daywise.app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret-key-that-is-long-enough",
            SQLALCHEMY_DATABASE_URI=(
                f"sqlite:///{os.path.join(cls.temp_dir.name, 'test.db')}"
            ),
            UPLOAD_FOLDER=cls.upload_dir,
            STORAGE_BACKEND="local",
            SUPABASE_URL="https://example.supabase.co",
            SUPABASE_SERVICE_ROLE_KEY="test-service-role-key",
            SUPABASE_STORAGE_BUCKET="daywise-files",
        )
        with daywise.app.app_context():
            daywise.db.create_all()

    @classmethod
    def tearDownClass(cls):
        with daywise.app.app_context():
            daywise.db.session.remove()
            daywise.db.drop_all()
            daywise.db.engine.dispose()
        cls.temp_dir.cleanup()

    def setUp(self):
        daywise.app.config["STORAGE_BACKEND"] = "local"
        with daywise.app.app_context():
            daywise.db.session.remove()
            daywise.db.drop_all()
            daywise.db.create_all()
            self.user = daywise.User(
                name="Owner",
                email="owner@example.com",
                password_hash=generate_password_hash("correct-password"),
            )
            self.other_user = daywise.User(
                name="Another User",
                email="another@example.com",
                password_hash=generate_password_hash("other-password"),
            )
            daywise.db.session.add_all([self.user, self.other_user])
            daywise.db.session.commit()
            self.user_id = self.user.id
            self.other_user_id = self.other_user.id
        self.client = daywise.app.test_client()

    def tearDown(self):
        with daywise.app.app_context():
            daywise.db.session.remove()
        daywise.app.config["STORAGE_BACKEND"] = "local"

    def sign_in_as(self, user_id):
        with self.client.session_transaction() as user_session:
            user_session["user_id"] = user_id

    def create_other_users_assignment(self):
        with daywise.app.app_context():
            assignment = daywise.Assignment(
                title="Private assignment",
                subject=daywise.SUBJECT_OPTIONS[0],
                due_date=date.today(),
                user_id=self.other_user_id,
            )
            assignment.subtasks = [daywise.SubTask(title="Private subtask")]
            daywise.db.session.add(assignment)
            daywise.db.session.commit()
            return assignment.id, assignment.subtasks[0].id

    def test_local_configuration_and_database_url_normalization(self):
        self.assertEqual(daywise.app.config["STORAGE_BACKEND"], "local")
        self.assertTrue(daywise.app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///"))
        self.assertFalse(daywise.app.config["SESSION_COOKIE_SECURE"])
        self.assertTrue(daywise.app.config["SESSION_COOKIE_HTTPONLY"])

        normalized = daywise.normalize_database_url(
            "postgres://db-user:p%40ss@db.example.test:5432/daywise"
        )
        self.assertEqual(normalized.drivername, "postgresql+psycopg")
        self.assertEqual(normalized.query["sslmode"], "require")
        self.assertEqual(normalized.password, "p@ss")
        supplied_ssl = daywise.normalize_database_url(
            "postgresql://db-user:secret@db.example.test/daywise?sslmode=verify-full"
        )
        self.assertEqual(supplied_ssl.query["sslmode"], "verify-full")
        insecure_ssl = daywise.normalize_database_url(
            "postgres://db-user:secret@db.example.test/daywise?sslmode=disable"
        )
        self.assertEqual(insecure_ssl.query["sslmode"], "require")
        with self.assertRaisesRegex(RuntimeError, "must use PostgreSQL"):
            daywise.normalize_database_url("mysql://db.example.test/daywise")
        with self.assertRaisesRegex(RuntimeError, "random SECRET_KEY"):
            daywise.validate_production_secret(
                "replace-with-a-random-value-at-least-32-characters"
            )
        with self.assertRaisesRegex(RuntimeError, "random SECRET_KEY"):
            daywise.validate_production_secret(
                "studysync-local-development-secret"
            )
        self.assertEqual(
            daywise.validate_production_secret("a" * 48),
            "a" * 48,
        )
        with self.assertRaisesRegex(RuntimeError, "SUPABASE_URL"):
            daywise.validate_production_storage(
                "https://your-project.supabase.co",
                "replace-with-your-server-side-service-role-key",
            )
        daywise.validate_production_storage(
            "https://sample.supabase.co",
            "test-service-role-key",
        )

    def test_login_hashes_password_and_health_check_is_public(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})
        self.assertEqual(self.client.get("/").status_code, 302)

        response = self.client.post(
            "/login",
            data={"email": "owner@example.com", "password": "correct-password"},
        )
        self.assertEqual(response.status_code, 302)
        with daywise.app.app_context():
            user = daywise.db.session.get(daywise.User, self.user_id)
            self.assertTrue(check_password_hash(user.password_hash, "correct-password"))
            self.assertNotEqual(user.password_hash, "correct-password")
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_signup_login_and_persistent_same_device_session(self):
        email = "New.User@Example.com"
        password = "new-account-password"
        response = self.client.post(
            "/signup",
            data={"name": "New User", "email": email, "password": password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")
        self.assertIn("Expires=", response.headers["Set-Cookie"])
        with self.client.session_transaction() as user_session:
            self.assertTrue(user_session.permanent)
            signed_up_user_id = user_session["user_id"]
        self.assertEqual(self.client.get("/").status_code, 200)

        self.client.post("/logout")
        self.assertEqual(self.client.get("/").status_code, 302)
        response = self.client.post(
            "/login",
            data={"email": email.upper(), "password": password},
        )

        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as user_session:
            self.assertTrue(user_session.permanent)
            self.assertEqual(user_session["user_id"], signed_up_user_id)
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_local_upload_download_delete_and_cross_user_file_denial(self):
        self.sign_in_as(self.user_id)
        response = self.client.post(
            "/upload-file",
            data={
                "subject": daywise.SUBJECT_OPTIONS[0],
                "file": (BytesIO(b"private file bytes"), "notes.pdf"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        with daywise.app.app_context():
            uploaded_file = daywise.UploadedFile.query.filter_by(
                user_id=self.user_id
            ).one()
            file_id = uploaded_file.id
            stored_path = daywise.local_storage_path(uploaded_file.stored_filename)
        self.assertTrue(os.path.isfile(stored_path))

        download = self.client.get(f"/download-file/{file_id}")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, b"private file bytes")
        self.assertEqual(download.headers["Cache-Control"], "private, no-store")

        with daywise.app.app_context():
            another_file = daywise.UploadedFile(
                filename="other.pdf",
                stored_filename="other-user.pdf",
                user_id=self.other_user_id,
            )
            daywise.db.session.add(another_file)
            daywise.db.session.commit()
            other_file_id = another_file.id
            other_path = daywise.local_storage_path(another_file.stored_filename)
            with open(other_path, "wb") as stored_file:
                stored_file.write(b"other user's bytes")

        self.assertEqual(self.client.get(f"/download-file/{other_file_id}").status_code, 404)
        self.assertEqual(
            self.client.post(f"/delete-file/{other_file_id}").status_code, 404
        )
        self.assertTrue(os.path.isfile(other_path))
        self.assertEqual(self.client.post(f"/delete-file/{file_id}").status_code, 302)
        self.assertFalse(os.path.isfile(stored_path))

    def test_subtask_routes_enforce_assignment_ownership(self):
        self.sign_in_as(self.user_id)
        assignment_id, subtask_id = self.create_other_users_assignment()

        self.assertEqual(self.client.get(f"/edit-assignment/{assignment_id}").status_code, 404)
        self.assertEqual(
            self.client.post(f"/add-subtask/{assignment_id}", data={"title": "New"}).status_code,
            404,
        )
        self.assertEqual(self.client.post(f"/toggle-subtask/{subtask_id}").status_code, 404)
        self.assertEqual(self.client.post(f"/delete-subtask/{subtask_id}").status_code, 404)
        self.assertEqual(
            self.client.post(f"/complete-assignment/{assignment_id}").status_code, 404
        )
        self.assertEqual(
            self.client.post(f"/delete-assignment/{assignment_id}").status_code, 404
        )

        with daywise.app.app_context():
            assignment = daywise.db.session.get(daywise.Assignment, assignment_id)
            self.assertEqual(len(assignment.subtasks), 1)
            self.assertFalse(assignment.subtasks[0].completed)

    def test_avatar_route_only_serves_signed_in_users_avatar(self):
        with daywise.app.app_context():
            owner = daywise.db.session.get(daywise.User, self.user_id)
            another_user = daywise.db.session.get(daywise.User, self.other_user_id)
            owner.avatar_filename = "owner-avatar.png"
            another_user.avatar_filename = "other-avatar.png"
            daywise.db.session.commit()
            for filename, contents in (
                ("owner-avatar.png", b"owner image"),
                ("other-avatar.png", b"other image"),
            ):
                with open(daywise.local_storage_path(filename), "wb") as avatar:
                    avatar.write(contents)

        self.sign_in_as(self.user_id)
        response = self.client.get("/profile/avatar")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"owner image")
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        self.assertEqual(self.client.get("/profile/avatar?user_id=2").data, b"owner image")

    def test_cloud_storage_uses_private_user_paths_and_server_side_downloads(self):
        bucket = Mock()
        bucket.download.return_value = b"cloud file bytes"
        self.sign_in_as(self.user_id)
        daywise.app.config["STORAGE_BACKEND"] = "supabase"
        with patch("app.supabase_storage_bucket", return_value=bucket):
            response = self.client.post(
                "/upload-file",
                data={
                    "file": (BytesIO(b"cloud file bytes"), "cloud.pdf"),
                    "subject": daywise.SUBJECT_OPTIONS[0],
                },
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 302)

            with daywise.app.app_context():
                uploaded_file = daywise.UploadedFile.query.filter_by(
                    user_id=self.user_id
                ).one()
                file_id = uploaded_file.id
                storage_path = uploaded_file.stored_filename
            self.assertTrue(storage_path.startswith(f"users/{self.user_id}/files/"))
            self.assertLessEqual(len(storage_path), 255)
            self.assertEqual(bucket.upload.call_args.args[0], storage_path)
            self.assertEqual(bucket.upload.call_args.kwargs["file_options"]["upsert"], "false")

            response = self.client.get(f"/download-file/{file_id}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b"cloud file bytes")
            self.assertEqual(bucket.download.call_args.args[0], storage_path)

            self.assertEqual(self.client.post(f"/delete-file/{file_id}").status_code, 302)
            bucket.remove.assert_called_once_with([storage_path])

    def test_cloud_avatar_upload_and_access_stay_owner_bound(self):
        bucket = Mock()
        bucket.download.return_value = b"\x89PNG\r\n\x1a\ncloud avatar"
        self.sign_in_as(self.user_id)
        daywise.app.config["STORAGE_BACKEND"] = "supabase"
        with patch("app.supabase_storage_bucket", return_value=bucket):
            response = self.client.post(
                "/profile",
                data={
                    "name": "Owner",
                    "bio": "Profile",
                    "avatar": (
                        BytesIO(b"\x89PNG\r\n\x1a\ncloud avatar"),
                        "avatar.png",
                    ),
                },
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 302)

            with daywise.app.app_context():
                owner = daywise.db.session.get(daywise.User, self.user_id)
                stored_avatar = owner.avatar_filename
            self.assertTrue(stored_avatar.startswith(f"users/{self.user_id}/avatars/"))
            self.assertEqual(bucket.upload.call_args.args[0], stored_avatar)

            response = self.client.get("/profile/avatar")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b"\x89PNG\r\n\x1a\ncloud avatar")
            self.assertEqual(bucket.download.call_args.args[0], stored_avatar)


if __name__ == "__main__":
    unittest.main()
