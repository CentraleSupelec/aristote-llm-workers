import json

import click


def deduplicate_lines(transcripts):
    new_transcripts = transcripts.copy()
    for i in range(0, len(transcripts) - 2):
        index_1 = len(transcripts) - 1 - i
        index_2 = len(transcripts) - 2 - i
        index_3 = len(transcripts) - 3 - i

        if (
            transcripts[index_3] == transcripts[index_1][: len(transcripts[index_3])]
            and transcripts[index_2] == ""
        ):
            new_transcripts[index_3 : index_1 + 1] = [
                transcripts[index_2],
                transcripts[index_3],
            ]
    return new_transcripts


@click.command()
@click.option("--input_file", type=str)
@click.option("--output_file", type=str)
def main(input_file, output_file):
    transcripts = []
    with open(input_file, "r") as f:
        for line in f:
            transcripts.append(line.strip())

        transcripts = deduplicate_lines(transcripts)

        transcripts = [t if t != "" else "\n" for t in transcripts]
        transcripts = " ".join(transcripts)
        transcripts = transcripts.split("\n")
        transcripts = [t.strip() for t in transcripts]
    with open(output_file, "w") as f:
        json.dump({"transcripts": transcripts}, f, indent=4)


if __name__ == "__main__":
    main()
