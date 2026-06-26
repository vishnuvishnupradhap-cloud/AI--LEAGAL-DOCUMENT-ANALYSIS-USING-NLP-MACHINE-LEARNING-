import traceback
with open('error.txt', 'w') as f:
    try:
        from transformers import AutoModelForSeq2SeqLM
        model = AutoModelForSeq2SeqLM.from_pretrained('humarin/chatgpt_paraphraser_on_T5_base')
        f.write("Success")
    except Exception as e:
        f.write(traceback.format_exc())
