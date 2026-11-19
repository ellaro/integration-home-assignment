const form = document.getElementById("converter-form");
const dateInput = document.getElementById("gregorian-date");
const sunsetInput = document.getElementById("after-sunset");
const button = document.getElementById("convert-button");
const loading = document.getElementById("loading");
const errorMessage = document.getElementById("error-message");
const result = document.getElementById("result");
const toggleText = document.getElementById("toggle-text");

sunsetInput.addEventListener("change", () => {
    toggleText.textContent = sunsetInput.checked ? "After Sunset" : "Day Time";
});

const today = new Date();
const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000)
    .toISOString().slice(0, 10);
dateInput.value = localToday;

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    loading.classList.add("active");
    errorMessage.className = "status";
    errorMessage.textContent = "";
    result.classList.remove("active");

    try {
        const response = await fetch("/api/convert", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                date: dateInput.value,
                afterSunset: sunsetInput.checked
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error?.message || "We couldn't convert that date.");
        }

        const parts = data.heDateParts || {};
        document.getElementById("hebrew-date").textContent = data.hebrew || "Unavailable";
        document.getElementById("hebrew-day").textContent = parts.day || "-";
        document.getElementById("hebrew-month").textContent = parts.month || "-";
        document.getElementById("hebrew-year").textContent = parts.year || "-";

        const events = data.events && data.events.length
            ? data.events.join(", ")
            : "No special events";
        document.getElementById("events").innerHTML =
            "<strong>Special events:</strong> " + escapeHtml(events);
        result.classList.add("active");
    } catch (error) {
        errorMessage.textContent = error.message || "Something went wrong. Please try again.";
        errorMessage.className = "status error";
    } finally {
        loading.classList.remove("active");
        button.disabled = false;
    }
});

function escapeHtml(value) {
    const element = document.createElement("span");
    element.textContent = value;
    return element.innerHTML;
}
