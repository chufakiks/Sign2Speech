"""
SignWriting to text translation service.

Uses the sockeye-signwriting-to-text model from HuggingFace
to translate SignWriting notation to English text.
"""

from functools import lru_cache
from signwriting.tokenizer import SignWritingTokenizer
from signwriting_translation.bin import load_sockeye_translator, translate


# Model ID on HuggingFace
MODEL_ID = "sign/sockeye-signwriting-to-text"

# SignWriting tokenizer
sw_tokenizer = SignWritingTokenizer()


@lru_cache(maxsize=1)
def get_translator():
    """Load and cache the translation model."""
    translator, _ = load_sockeye_translator(MODEL_ID, log_timing=True)
    return translator


def signwriting_to_text(signwriting: str, target_language: str = "en") -> str:
    """
    Translate SignWriting notation to text.

    Args:
        signwriting: SignWriting FSW string (e.g., "M500x500S33100482x483...")
        target_language: Target language code (default: "en" for English)

    Returns:
        Translated text string
    """
    translator = get_translator()

    # Tokenize the SignWriting
    tokenized = " ".join(sw_tokenizer.text_to_tokens(signwriting))

    # Add language prefix
    model_input = f"${target_language} {tokenized}"

    # Translate
    outputs = translate(translator, [model_input])

    # Clean up BPE tokens (remove @@ markers)
    text = outputs[0].replace("@@", "")

    return text


def translate_signs(signwriting_list: list[str], target_language: str = "en") -> list[str]:
    """
    Translate multiple SignWriting strings to text in batch.

    Args:
        signwriting_list: List of SignWriting FSW strings
        target_language: Target language code (default: "en" for English)

    Returns:
        List of translated text strings
    """
    if not signwriting_list:
        return []

    translator = get_translator()

    # Prepare all inputs
    model_inputs = []
    for sw in signwriting_list:
        tokenized = " ".join(sw_tokenizer.text_to_tokens(sw))
        model_inputs.append(f"${target_language} {tokenized}")

    # Batch translate
    outputs = translate(translator, model_inputs)

    # Clean up BPE tokens
    return [out.replace("@@", "") for out in outputs]
