document.addEventListener("DOMContentLoaded", () => {
    console.log("Survey script initialized successfully!");

    let questionCounter = 1;

    // Add option functionality
    document.addEventListener("click", (event) => {
        if (event.target.classList.contains("add-option-btn")) {
            console.log("Add Option button clicked");

            const questionId = event.target.dataset.questionId;
            const optionsContainer = document.getElementById(`options-container-${questionId}`);

            if (optionsContainer) {
                const optionCount = optionsContainer.childElementCount + 1;
                const optionWrapper = document.createElement("div");
                optionWrapper.className = "option-wrapper";
                optionWrapper.setAttribute("aria-label", `Option ${optionCount} for Question ${questionId}`);

                const newOption = document.createElement("input");
                newOption.type = "text";
                newOption.name = `questions[${questionId}][options][]`;
                newOption.placeholder = `Option ${optionCount}`;
                newOption.className = "option-input";
                newOption.required = true;

                const removeOptionBtn = document.createElement("button");
                removeOptionBtn.type = "button";
                removeOptionBtn.className = "remove-option-btn btn btn-danger";
                removeOptionBtn.textContent = "Remove Option";
                removeOptionBtn.setAttribute("aria-label", `Remove Option ${optionCount} for Question ${questionId}`);

                optionWrapper.appendChild(newOption);
                optionWrapper.appendChild(removeOptionBtn);
                optionsContainer.appendChild(optionWrapper);

                console.log(`Option ${optionCount} added successfully to Question ${questionId}`);
            } else {
                console.error(`Options container not found for Question ID: ${questionId}`);
            }
        }

        // Remove option functionality
        if (event.target.classList.contains("remove-option-btn")) {
            const optionWrapper = event.target.parentElement;
            if (optionWrapper) {
                if (confirm("Are you sure you want to remove this option?")) {
                    optionWrapper.remove();
                    console.log("Option removed successfully");
                }
            } else {
                console.error("Option wrapper not found");
            }
        }
    });

    // Add question functionality
    const addQuestionBtn = document.getElementById("add-question-btn");
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener("click", () => {
            questionCounter++;
            console.log(`Adding new question: Question ${questionCounter}`);

            const questionsContainer = document.getElementById("questions-container");
            if (questionsContainer) {
                const newQuestion = document.createElement("div");
                newQuestion.className = "question";
                newQuestion.setAttribute("id", `question-${questionCounter}`);
                newQuestion.setAttribute("aria-label", `Question ${questionCounter}`);

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
                        <div class="option-wrapper">
                            <input type="text" name="questions[${questionCounter}][options][]" placeholder="Option 1" required>
                            <button type="button" class="remove-option-btn btn btn-danger">Remove Option</button>
                        </div>
                        <button type="button" class="add-option-btn btn btn-success" data-question-id="${questionCounter}">Add Option</button>
                    </div>
                `;

                questionsContainer.appendChild(newQuestion);
                console.log(`Question ${questionCounter} added successfully`);
            } else {
                console.error("Questions container not found");
            }
        });
    } else {
        console.error("Add Question button not found");
    }

    // Save as Draft
    const saveDraftBtn = document.getElementById("save-draft-btn");
    if (saveDraftBtn) {
        saveDraftBtn.addEventListener("click", () => {
            console.log("Save as Draft button clicked");
            document.getElementById("survey-status").value = "draft";
            document.getElementById("survey-form").submit();
            console.log("Survey saved as draft.");
        });
    }

    // Publish
    const publishBtn = document.getElementById("publish-btn");
    if (publishBtn) {
        publishBtn.addEventListener("click", () => {
            console.log("Publish button clicked");
            document.getElementById("survey-status").value = "published";
            document.getElementById("survey-form").submit();
            console.log("Survey published successfully.");
        });
    }
});
