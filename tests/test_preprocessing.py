from typing import List

import pytest
from transformers import AutoTokenizer

from quiz_generation.dtos.dtos import TranscribedText
from quiz_generation.preprocessing.preprocessing import (
    get_splits,
    get_token_nb,
    load_txt,
)


@pytest.mark.parametrize(
    "path, expected_texts",
    [
        [
            "tests/example/bio_transcript.txt",
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
def test_load_txt(path: str, expected_texts: List[str]) -> None:
    transcripts = load_txt(path)
    assert isinstance(transcripts[0], TranscribedText)
    assert len(transcripts) == len(expected_texts)
    assert all(
        [
            transcript.text == expected_text
            for transcript, expected_text in zip(transcripts, expected_texts)
        ]
    )


@pytest.mark.parametrize(
    "transcripts, tokenizer_name, max_length, expected_splits",
    [
        [
            [
                TranscribedText(
                    text="the the the the the",
                    start=0,
                    end=1,
                ),
            ],
            "mistralai/Mistral-7B-v0.1",
            2,
            [
                TranscribedText(
                    text="the",
                    start=0,
                    end=0.2,
                ),
                TranscribedText(
                    text="the",
                    start=0.2,
                    end=0.4,
                ),
                TranscribedText(
                    text="the",
                    start=0.4,
                    end=0.6,
                ),
                TranscribedText(
                    text="the",
                    start=0.6,
                    end=0.8,
                ),
                TranscribedText(
                    text="the",
                    start=0.8,
                    end=1,
                ),
            ],
        ],
        [
            [
                TranscribedText(text="[Music]"),
                TranscribedText(text="okay today we are on the last section of"),
                TranscribedText(text="chapter 9 section 9.3 we're still"),
                TranscribedText(text="talking about energy but today we're not"),
                TranscribedText(text="gonna talk about energy in plants we're"),
                TranscribedText(text="gonna talk about cellular respiration"),
                TranscribedText(text="we're gonna talk about how that process"),
                TranscribedText(text="works and I talked about photosynthesis"),
                TranscribedText(text="we're talking about cellular respiration"),
            ],
            "mistralai/Mistral-7B-v0.1",
            30,
            [
                TranscribedText(
                    text=(
                        "[Music] okay today we are on the last section of chapter 9 "
                        "section 9.3 we're still"
                    )
                ),
                TranscribedText(
                    text=(
                        "talking about energy but today we're not gonna talk about "
                        "energy in plants we're gonna talk about cellular respiration"
                    )
                ),
                TranscribedText(
                    text=(
                        "we're gonna talk about how that process works and "
                        "I talked about photosynthesis"
                    )
                ),
                TranscribedText(text="we're talking about cellular respiration"),
            ],
        ],
    ],
)
def test_get_splits(
    transcripts: List[TranscribedText],
    tokenizer_name: str,
    max_length: int,
    expected_splits: List[TranscribedText],
) -> None:
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    splits = get_splits(transcripts, tokenizer, max_length)
    print(splits)
    assert isinstance(splits[0], TranscribedText)
    assert len(splits) == len(expected_splits)
    assert all([get_token_nb(split.text, tokenizer) <= max_length for split in splits])
    assert all(
        [
            split.text == expected_split.text
            for split, expected_split in zip(splits, expected_splits)
        ]
    )
    assert all(
        [
            split.start == pytest.approx(expected_split.start)
            and split.end == pytest.approx(expected_split.end)
            for split, expected_split in zip(splits, expected_splits)
        ]
    )
