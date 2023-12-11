
import os
import logging
from app import configure_logging
from llama_cpp.llama import Llama, LlamaGrammar



logger = logging.getLogger(__name__)

grammar_text = """
root ::= Advisory
FireZone ::= "{"   ws   "\"id\":"   ws   string   ","   ws   "\"name\":"   ws   string   ","   ws   "\"fuelType\":"   ws   FuelType   "}"
FireZonelist ::= "[]" | "["   ws   FireZone   (","   ws   FireZone)*   "]"
FuelType ::= "\"C1\"" | "\"C2\"" | "\"C3\""
Advisory ::= "{"   ws   "\"id\":"   ws   string   ","   ws   "\"fireZone\":"   ws   FireZone   ","   ws   "\"percentageCombustable\":"   ws   number   "}"
Advisorylist ::= "[]" | "["   ws   Advisory   (","   ws   Advisory)*   "]"
string ::= "\""   ([^"]*)   "\""
boolean ::= "true" | "false"
ws ::= [ \t\n]*
number ::= [0-9]+   "."?   [0-9]*
stringlist ::= "["   ws   "]" | "["   ws   string   (","   ws   string)*   ws   "]"
numberlist ::= "["   ws   "]" | "["   ws   string   (","   ws   number)*   ws   "]"

"""

def main():
    """ main script - process and download models, then do exception handling """

    prompt = "A fire weather advisory with winds of 30km/hr, temperature 27 degrees celcius and wind direction from the southeast"
    logger.info("Generating advisory")
    grammer_path = os.path.join(os.path.dirname(__file__), 'grammar.gbnf')
    with open(grammer_path, 'r') as grammer_file:
        grammar_text = grammer_file.read()
        llm = Llama("/Users/cbrady/mistral-7b-openorca.Q5_K_S.gguf")
        grammar = LlamaGrammar.from_string(grammar_text)
        response = llm(prompt, grammar=grammar)
        logger.info(response)



if __name__ == "__main__":
    configure_logging()
    main()