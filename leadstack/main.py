import argparse

from dotenv import load_dotenv

from src.dedup import stack_lists

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Merge and deduplicate real-estate lead lists from multiple providers."
    )
    parser.add_argument("csv_files", nargs="+", help="Input CSV files to stack")
    parser.add_argument("-o", "--output", default="stacked_leads.csv", help="Output CSV path")
    args = parser.parse_args()

    df = stack_lists(args.csv_files)
    df.to_csv(args.output, index=False)
    print(f"Stacked {len(args.csv_files)} lists into {len(df)} unique leads -> {args.output}")


if __name__ == "__main__":
    main()
