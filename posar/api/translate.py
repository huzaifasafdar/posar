import frappe
from googletrans import Translator

@frappe.whitelist()
def translate_to_arabic(text):
    translator = Translator()
    translated = translator.translate(text, src='en', dest='ar').text
    return translated