
import logging
from app import configure_logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers import GPT2Tokenizer, GPT2Model, GPT2LMHeadModel


logger = logging.getLogger(__name__)

def main():
    """ main script - process and download models, then do exception handling """
    logger.info("Generating advisory")
    # model_name = 'Intel/neural-chat-7b-v3-1'
    # model = AutoModelForCausalLM.from_pretrained(model_name)
    # tokenizer = AutoTokenizer.from_pretrained(model_name)

    prompt = "A fire weather advisory with winds of 30km/hr, temperature 27 degrees celcius and wind direction from the southeast"
    # inputs = tokenizer.encode(prompt, return_tensors="pt", add_special_tokens=False)
    # outputs = model.generate(inputs, max_length=1000, num_return_sequences=1)
    # response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # logger.info(response)

    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    text = "Replace me by any text you'd like."
    inputs = tokenizer.encode(prompt, return_tensors="pt", add_special_tokens=False)
    outputs = model.generate(inputs, max_length=1000, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # encoded_input = tokenizer(text, return_tensors='pt')
    # output = model(**encoded_input)
    logger.info(response)


if __name__ == "__main__":
    configure_logging()
    main()