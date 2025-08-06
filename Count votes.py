import csv


class MP:
    """
    Represents a single Member of Parliament.
    It stores personal details and their party affiliation.
    """
    def __init__(self, first_name, surname, gender, party):
        self.full_name = f"{first_name} {surname}"
        self.gender = gender
        self.party = party

    def __str__(self):
        return f"{self.full_name} ({self.party})"

class Constituency:
    """
    Represents a single parliamentary seat (constituency).
    This class holds all data for one row of the CSV, including the winning MP
    object and a dictionary for all vote counts.
    """
    def __init__(self, name, region, country, electorate, valid_votes, majority, winning_mp, vote_counts):
        self.name = name
        self.region = region
        self.country = country
        self.electorate = electorate  
        self.valid_votes = valid_votes  
        self.majority = majority
        self.winning_mp = winning_mp 
        self.vote_counts = vote_counts  

    def get_winning_candidate_votes(self):
        """Returns the number of votes for the winning candidate."""
        return self.vote_counts.get(self.winning_mp.party, 0)

    def get_party_percentage(self, party_abbr):
        """Calculates and returns the vote percentage for a given party."""
        party_votes = self.vote_counts.get(party_abbr, 0)
        if self.valid_votes == 0:
            return 0.0
        return (party_votes / self.valid_votes) * 100

    def display_details(self):
        """Provides a formatted string of all key details for this constituency."""
        turnout = (self.valid_votes / self.electorate * 100) if self.electorate > 0 else 0
        details = (
            f"\n--- Details for {self.name} ---\n"
            f"  Parliamentary Seat: {self.name}\n"
            f"  Region: {self.region}, {self.country}\n\n"
            f"  Winning Candidate: {self.winning_mp.full_name}\n"
            f"  Candidate's Party: {self.winning_mp.party}\n"
            f"  Votes for Candidate: {self.get_winning_candidate_votes():,}\n\n"
            f"  Total Registered Voters: {self.electorate:,}\n"
            f"  Total Votes Cast: {self.valid_votes:,} (Turnout: {turnout:.2f}%)\n"
            f"  Majority: {self.majority:,}\n"
        )
        return details

class Party:
    """
    Aggregates data for a political party across all constituencies.
    Uses a list as a container for its elected MPs.
    """
    def __init__(self, abbreviation):
        self.abbreviation = abbreviation
        self.total_votes = 0
        self.seats_won = 0
        self.mps = []  

    def add_seat(self, mp_object):
        """Registers a win for this party and adds the MP."""
        self.seats_won += 1
        self.mps.append(mp_object)

    def add_votes(self, count):
        """Adds votes from a constituency to the national total."""
        self.total_votes += count


def load_data(filename="election_results.csv"):
    """
    Reads the CSV file, creating and populating objects for each class.
    Handles file errors and malformed rows gracefully.
    Returns two dictionaries for efficient lookup: constituencies and parties.
    """
    constituencies = {}
    parties = {}
    party_columns = ['Con', 'Lab', 'LD', 'RUK', 'Green', 'SNP', 'PC', 'DUP', 'SF', 'SDLP', 'UUP', 'APNI', 'All other']

    try:
        with open(filename, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not row or not row.get('Constituency name', '').strip():
                    continue

                try:
                    constituency_name = row['Constituency name'].strip()
                    winning_party_abbr = row['Result'].strip()
                    winning_mp = MP(
                        first_name=row['Member first name'].strip(),
                        surname=row['Member surname'].strip(),
                        gender=row['Member gender'].strip(),
                        party=winning_party_abbr
                    )
                    vote_counts = {}
                    for party_abbr in party_columns:
                        if party_abbr in row:
                            votes_str = row[party_abbr].strip().replace(',', '')
                            if votes_str.isdigit():
                                votes = int(votes_str)
                                vote_counts[party_abbr] = votes
                                if party_abbr not in parties:
                                    parties[party_abbr] = Party(party_abbr)
                                parties[party_abbr].add_votes(votes)
                    
                    constituency_obj = Constituency(
                        name=constituency_name,
                        region=row['Region'].strip(),
                        country=row['Country'].strip(),
                        electorate=int(row['Electorate'].replace(',', '')),
                        valid_votes=int(row['Valid votes'].replace(',', '')),
                        majority=int(row['Majority'].replace(',', '')),
                        winning_mp=winning_mp,
                        vote_counts=vote_counts
                    )
                    
                    constituencies[constituency_name.lower()] = constituency_obj
                    
                    if winning_party_abbr not in parties:
                        parties[winning_party_abbr] = Party(winning_party_abbr)
                    parties[winning_party_abbr].add_seat(winning_mp)

                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping row for '{row.get('Constituency name', 'Unknown')}' due to data error: {e}")

    except FileNotFoundError:
        print(f"FATAL ERROR: The file '{filename}' was not found.")
        return None, None
    
    print(f"Successfully loaded data for {len(constituencies)} constituencies.")
    return constituencies, parties

def save_statistics(filename, constituencies, parties):
    """Calculates summary statistics and saves them to a file upon exit."""
    if not constituencies or not parties:
        print("No data to save.")
        return

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("--- UK General Election Summary Statistics ---\n\n")

            total_winning_votes = sum(c.get_winning_candidate_votes() for c in constituencies.values())
            avg_winning_votes = total_winning_votes / len(constituencies) if constituencies else 0
            f.write(f"Average votes needed for a candidate to be elected: {avg_winning_votes:,.0f}\n")

            total_winning_percent = sum(c.get_party_percentage(c.winning_mp.party) for c in constituencies.values())
            avg_winning_percent = total_winning_percent / len(constituencies) if constituencies else 0
            f.write(f"Average percentage of votes for a winning candidate: {avg_winning_percent:.2f}%\n\n")

            f.write("--- Gender Breakdown of Elected MPs by Party ---\n")
            for party_abbr, party_obj in sorted(parties.items()):
                if party_obj.seats_won > 0:
                    total_mps = party_obj.seats_won
                    male_mps = sum(1 for mp in party_obj.mps if mp.gender == 'Male')
                    female_mps = sum(1 for mp in party_obj.mps if mp.gender == 'Female')
                    male_perc = (male_mps / total_mps * 100) if total_mps > 0 else 0
                    female_perc = (female_mps / total_mps * 100) if total_mps > 0 else 0
                    f.write(
                        f"Party: {party_abbr} ({total_mps} seats)\n"
                        f"  - Male:   {male_mps} MPs ({male_perc:.1f}%)\n"
                        f"  - Female: {female_mps} MPs ({female_perc:.1f}%)\n"
                    )

        print(f"\nSummary statistics successfully saved to '{filename}'.")
    except IOError as e:
        print(f"Error: Could not write statistics to file '{filename}'. Reason: {e}")


def print_menu():
    """Displays the main menu to the user."""
    print("\n" + "="*40)
    print("    UK Election Data Explorer Menu")
    print("="*40)
    print("1. Enquire about a Parliamentary Seat")
    print("2. Enquire about a Candidate (MP)")
    print("3. Get party vote percentage in a seat")
    print("4. Exit and Save Statistics")
    print("="*40)

def main():
    """The main function to run the application."""
    constituencies, parties = load_data()
    
    if constituencies is None: 
        return

    while True:
        print_menu()
        try:
            choice = input("Enter your choice (1-4): ").strip()

            if choice == '1':
                # Covers: Seat name, registered voters, total votes, candidate name, candidate party, votes for candidate
                name = input("Enter constituency (seat) name: ").lower().strip()
                constituency = constituencies.get(name)
                if constituency:
                    print(constituency.display_details())
                else:
                    print("Error: Constituency not found.")

            elif choice == '2':
                # Covers: Candidate party, candidate name
                name_query = input("Enter winning candidate's full name: ").lower().strip()
                found_mp = False
                for c in constituencies.values():
                    if name_query == c.winning_mp.full_name.lower():
                        print(f"\n--- Candidate Found ---")
                        print(f"  Candidate Name: {c.winning_mp.full_name}")
                        print(f"  Candidate Party: {c.winning_mp.party}")
                        print(f"  Parliamentary Seat: {c.name}")
                        found_mp = True
                        break
                if not found_mp:
                    print("Error: No winning MP found with that name.")

            elif choice == '3':
                # Covers: Votes for a given party as a percentage
                c_name = input("Enter constituency name: ").lower().strip()
                constituency = constituencies.get(c_name)
                if not constituency:
                    print("Error: Constituency not found.")
                    continue

                p_abbr = input("Enter party abbreviation (e.g., Con, Lab, SNP): ").strip()
                if p_abbr in constituency.vote_counts:
                    percentage = constituency.get_party_percentage(p_abbr)
                    votes = constituency.vote_counts[p_abbr]
                    print(f"\nIn {constituency.name}, the {p_abbr} party received {votes:,} votes.")
                    print(f"This is {percentage:.2f}% of the total votes cast.")
                else:
                    print(f"Error: Vote data for '{p_abbr}' not found in this constituency.")

            elif choice == '4':
                print("Calculating final statistics and exiting...")
                save_statistics("election_summary_stats.txt", constituencies, parties)
                print("Goodbye!")
                break

            else:
                print("Invalid choice. Please enter a number between 1 and 4.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}. Please try again.")

if __name__ == "__main__":
    main()