import pytest
from transformers import AutoTokenizer

from quiz_generation.preprocessing.preprocessing import (
    get_splits,
    get_token_nb,
    load_txt,
)


@pytest.mark.parametrize(
    "path, expected_texts",
    [
        [
            "data/tests/bio_transcript.txt",
            [
                "[Music]",
                "okay today we are on the last section of",
                "chapter 9 section 9.3 we're still",
                "talking about energy but today we're not",
                "gonna talk about energy in plants we're",
                "gonna talk about cellular respiration",
                "we're gonna talk about how that process",
                "works and I talked about photosynthesis",
                "we're talking about cellular respiration",
            ],
        ]
    ],
)
def test_load_txt(path, expected_texts):
    texts = load_txt(path)
    assert len(texts) == len(expected_texts)
    assert all(
        [text == expected_text for text, expected_text in zip(texts, expected_texts)]
    )


@pytest.mark.parametrize(
    "transcripts, tokenizer_name, max_length, expected_splits",
    [
        [
            [
                "the the the the the",
            ],
            "mistralai/Mistral-7B-v0.1",
            2,
            ["the", "the", "the", "the", "the"],
        ],
        [
            [
                "[Music]",
                "okay today we are on the last section of",
                "chapter 9 section 9.3 we're still",
                "talking about energy but today we're not",
                "gonna talk about energy in plants we're",
                "gonna talk about cellular respiration",
                "we're gonna talk about how that process",
                "works and I talked about photosynthesis",
                "we're talking about cellular respiration",
            ],
            "mistralai/Mistral-7B-v0.1",
            30,
            [
                "[Music] okay today we are on the last section of chapter 9 "
                "section 9.3 we're still",
                "talking about energy but today we're not gonna talk about energy in "
                "plants we're gonna talk about cellular respiration",
                "we're gonna talk about how that process works and "
                "I talked about photosynthesis",
                "we're talking about cellular respiration",
            ],
        ],
    ],
)
def test_get_splits(transcripts, tokenizer_name, max_length, expected_splits):
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    splits = get_splits(transcripts, tokenizer, max_length)
    assert len(splits) == len(expected_splits)
    assert all([get_token_nb(split, tokenizer) <= max_length for split in splits])
    assert all(
        [
            split == expected_split
            for split, expected_split in zip(splits, expected_splits)
        ]
    )
