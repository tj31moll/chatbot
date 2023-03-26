from datasets import Dataset

def prepare_dataset(input_file, output_file):
    with open(input_file, "r") as f:
        lines = f.readlines()

    examples = []
    for i in range(0, len(lines), 2):
        input_text = lines[i].strip()
        response = lines[i + 1].strip()
        examples.append({"input_text": input_text, "response": response})

    dataset = Dataset.from_dict(examples)
    dataset.save_to_disk(output_file)

if __name__ == "__main__":
    prepare_dataset("training_data.txt", "fine_tuning_dataset")
