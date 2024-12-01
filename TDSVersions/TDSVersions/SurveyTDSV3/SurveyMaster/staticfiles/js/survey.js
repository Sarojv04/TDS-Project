
document.addEventListener("DOMContentLoaded", () => {
    console.log("JavaScript is working");
    console.log("Survey script loaded successfully!");

    let questionCounter = 1;

    // Add option functionality
    document.addEventListener("click", (event) => {
        if (event.target.classList.contains("add-option-btn")) {
            console.log("Add Option button clicked");

            const questionId = event.target.dataset.questionId;
            console.log(`Adding option to question ID: ${questionId}`);

            const optionsContainer = document.getElementById(`options-container-${questionId}`);
            if (optionsContainer) {
                const newOption = document.createElement("input");
                newOption.type = "text";
                newOption.name = `questions[${questionId}][options][]`;
                newOption.placeholder = `Option ${optionsContainer.childElementCount + 1}`;
                newOption.className = "option-input";
                optionsContainer.appendChild(newOption);
                console.log(`Option added successfully to question ID: ${questionId}`);
            } else {
                console.error(`Options container not found for question ID: ${questionId}`);
            }
        }
    });

    // Add question functionality
    const addQuestionBtn = document.getElementById("add-question-btn");
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener("click", () => {
            console.log("Add Another Question button clicked");

            questionCounter++;
            console.log(`Creating new question number: ${questionCounter}`);

            const questionsContainer = document.getElementById("questions-container");
            if (questionsContainer) {
                const newQuestion = document.createElement("div");
                newQuestion.className = "question";
                newQuestion.innerHTML = `
                    <label for="question_${questionCounter}">Question ${questionCounter}:</label>
                    <input type="text" id="question_${questionCounter}" name="questions[${questionCounter}][text]" placeholder="Enter your question" required>
                    <label for="type_${questionCounter}">Type:</label>
                    <select id="type_${questionCounter}" name="questions[${questionCounter}][type]" required>
                        <option value="multiple_choice">Multiple Choice (Multiple Answers)</option>
                        <option value="single_choice">Single Choice</option>
                        <option value="text">Text Response</option>
                    </select>
                    <div id="options-container-${questionCounter}" class="options-container">
                        <label>Options:</label>
                        <input type="text" name="questions[${questionCounter}][options][]" placeholder="Option 1" required>
                        <button type="button" class="add-option-btn" data-question-id="${questionCounter}">Add Option</button>
                    </div>
                `;
                questionsContainer.appendChild(newQuestion);
                console.log(`New question added: Question ${questionCounter}`);
            } else {
                console.error("Questions container not found");
            }
        });
    } else {
        console.error("Add Question button not found");
    }
});


// Add a listener to log form submission
document.querySelector("form").addEventListener("submit", (event) => {
    console.log("Form submit event triggered!");
    const formData = new FormData(event.target);
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
});

document.querySelector("button[value='publish']").addEventListener("click", () => {
    console.log("Publish button clicked.");
    document.querySelector("form").submit();
});


document.addEventListener("DOMContentLoaded", () => {
    document.querySelector("form").addEventListener("submit", (event) => {
        console.log("Form submit event triggered!");
        console.log("Form data:", new FormData(event.target));
    });
});

