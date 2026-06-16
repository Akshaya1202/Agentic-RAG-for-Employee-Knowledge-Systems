const form = document.getElementById("query-form");
const queryInput = document.getElementById("query");
const answerBox = document.getElementById("answer");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  answerBox.textContent = "Thinking...";

  const response = await fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryInput.value }),
  });

  const data = await response.json();
  answerBox.textContent = data.answer;
});
