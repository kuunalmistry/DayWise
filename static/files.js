(() => {
  const page = document.querySelector(".files-page");
  if (!page) return;

  let recentFiles = page.querySelector(".recent-files");
  let resourceList = page.querySelector("#resourceList");
  let activeRequest;

  async function updateFiles(url, updateHistory) {
    activeRequest?.abort();
    const controller = new AbortController();
    activeRequest = controller;
    page.setAttribute("aria-busy", "true");

    try {
      const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`File filter request failed (${response.status}).`);

      const html = await response.text();
      const nextDocument = new DOMParser().parseFromString(html, "text/html");
      const nextRecentFiles = nextDocument.querySelector(".recent-files");
      const nextResourceList = nextDocument.querySelector("#resourceList");
      if (!nextRecentFiles || !nextResourceList || !recentFiles || !resourceList) {
        throw new Error("The filtered file results were not returned.");
      }

      recentFiles.replaceWith(nextRecentFiles);
      resourceList.replaceWith(nextResourceList);
      recentFiles = nextRecentFiles;
      resourceList = nextResourceList;
      if (updateHistory) window.history.pushState({}, "", url);
    } catch (error) {
      if (error.name === "AbortError") return;
      console.error(error);
      window.location.assign(url);
    } finally {
      if (activeRequest === controller) {
        activeRequest = undefined;
        page.removeAttribute("aria-busy");
      }
    }
  }

  function filteredUrl(link) {
    const nextUrl = new URL(window.location.href);
    const linkUrl = new URL(link.href, window.location.href);

    if (link.classList.contains("filter-chip")) {
      const category = linkUrl.searchParams.get("category");
      if (category) nextUrl.searchParams.set("category", category);
      else nextUrl.searchParams.delete("category");
    } else {
      const subject = linkUrl.searchParams.get("subject");
      if (subject) nextUrl.searchParams.set("subject", subject);
      else nextUrl.searchParams.delete("subject");
    }
    return nextUrl;
  }

  page.addEventListener("click", (event) => {
    const link = event.target.closest(".resource-controls .filter-chip, .folder-grid .folder-card");
    if (!link) return;

    event.preventDefault();
    const nextUrl = filteredUrl(link);
    if (nextUrl.href !== window.location.href) updateFiles(nextUrl.href, true);
  });

  window.addEventListener("popstate", () => updateFiles(window.location.href, false));
})();
