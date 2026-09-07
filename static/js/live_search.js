document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(
        "[data-live-search-form]"
    );

    const input = document.querySelector(
        "[data-live-search-input]"
    );

    const resultsContainer = document.querySelector(
        "[data-live-search-results]"
    );

    if (!form || !input || !resultsContainer) {
        return;
    }

    let timeoutId = null;
    let controller = null;

    async function loadResults(url) {
        if (controller) {
            controller.abort();
        }

        controller = new AbortController();

        resultsContainer.setAttribute(
            "aria-busy",
            "true"
        );

        try {
            const response = await fetch(
                url,
                {
                    headers: {
                        "X-Requested-With":
                            "XMLHttpRequest",
                    },
                    signal: controller.signal,
                }
            );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const html = await response.text();

            const parser = new DOMParser();

            const documentFromResponse =
                parser.parseFromString(
                    html,
                    "text/html"
                );

            const newResults =
                documentFromResponse.querySelector(
                    "[data-live-search-results]"
                );

            if (!newResults) {
                throw new Error(
                    "Не найден блок результатов."
                );
            }

            resultsContainer.innerHTML =
                newResults.innerHTML;

            history.replaceState(
                {},
                "",
                url
            );
        } catch (error) {
            if (error.name !== "AbortError") {
                console.error(
                    "Ошибка поиска:",
                    error
                );
            }
        } finally {
            resultsContainer.removeAttribute(
                "aria-busy"
            );
        }
    }

    function buildSearchUrl() {
        const url = new URL(
            window.location.href
        );

        const query = input.value.trim();

        if (query) {
            url.searchParams.set(
                "q",
                query
            );
        } else {
            url.searchParams.delete(
                "q"
            );
        }

        url.searchParams.delete(
            "page"
        );

        return url.toString();
    }

    input.addEventListener(
        "input",
        () => {
            clearTimeout(
                timeoutId
            );

            timeoutId = setTimeout(
                () => {
                    loadResults(
                        buildSearchUrl()
                    );
                },
                300
            );
        }
    );

    form.addEventListener(
        "submit",
        (event) => {
            event.preventDefault();

            clearTimeout(
                timeoutId
            );

            loadResults(
                buildSearchUrl()
            );
        }
    );

    resultsContainer.addEventListener(
        "click",
        (event) => {
            const link = event.target.closest(
                ".pagination a"
            );

            if (!link) {
                return;
            }

            event.preventDefault();

            loadResults(
                link.href
            );
        }
    );
});