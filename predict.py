from transformers import pipeline

def run_prediction(questions, context, model_path, n_best_size=3):
    """
    Runs Question Answering using Hugging Face pipelines.
    Args:
        questions (list): List of question strings.
        context (str): The context text (contract).
        model_path (str): Path or name of the model.
        n_best_size (int): Number of answers to return per question.
        
    Returns:
        list: A list of lists, where each inner list contains dictionaries for the top answers to a question.
              Example: [[{'answer': '...', 'score': 0.9}, ...], ...]
    """
    # Initialize the QA pipeline
    # We load the tokenizer specifically to handle potential fast/slow tokenizer conflicts automatically
    qa_pipeline = pipeline(
        "question-answering",
        model=model_path,
        tokenizer=model_path,
        device=-1  # Use CPU by default. Set to 0 to use GPU if available.
    )

    results = []
    
    # Process each question
    for question in questions:
        try:
            # top_k returns the top n answers
            # The pipeline handles tokenization and inference internally
            prediction = qa_pipeline(question=question, context=context, top_k=n_best_size)
            
            # If If top_k=1 it returns a dict, if >1 it returns a list of dicts. 
            # Normalize to list for consistency.
            if isinstance(prediction, dict):
                prediction = [prediction]
            
            # If nothing returned, ensure empty list
            if prediction is None:
                prediction = []
            
            # Deduplicate by answer text
            unique_predictions = []
            seen_answers = set()
            
            for pred in prediction:
                # Clean up whitespace for better deduping
                clean_answer = pred['answer'].strip()
                if clean_answer not in seen_answers:
                    seen_answers.add(clean_answer)
                    # Update dictionary with clean answer
                    pred['answer'] = clean_answer
                    unique_predictions.append(pred)
            
            results.append(unique_predictions)
        except Exception as e:
            print(f"Error processing question '{question}': {e}")
            results.append([])

    return results
