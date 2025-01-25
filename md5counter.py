import hashlib
import json
#import matplotlib.pyplot as plt

class StringMD5Counter:
    def __init__(self):
        """
        Initialize the StringMD5Counter with an empty dictionary.
        The keys will be MD5 hashes of strings, and the values will be counts of occurrences.
        """
        self.md5_count = {}

    def add_string(self, string):
        """
        Add a string to the counter and update its occurrence count.

        Args:
            string (str): The string to add.
        """
        # Calculate the MD5 hash of the string
        md5_hash = StringMD5Counter.hash(string)

        # Update the count for this hash
        if md5_hash in self.md5_count:
            self.md5_count[md5_hash] += 1
        else:
            self.md5_count[md5_hash] = 1

    @classmethod
    def hash(cls, s):
        return hashlib.md5(s.encode()).hexdigest()

    def get_count(self, string):
        """
        Get the count of occurrences for a given string.

        Args:
            string (str): The string to query.

        Returns:
            int: The count of occurrences for the string (0 if not present).
        """
        # Calculate the MD5 hash of the string
        md5_hash = hashlib.md5(string.encode()).hexdigest()

        # Return the count for this hash, or 0 if not found
        return self.md5_count.get(md5_hash, 0)

    def dump_to_file(self, file_path):
        """
        Save the current state of the counter to a file.

        Args:
            file_path (str): The path to the file where data will be saved.
        """
        with open(file_path, 'w') as file:
            json.dump(self.md5_count, file)

    @classmethod
    def load_from_file(cls, file_path):
        """
        Create an instance of StringMD5Counter initialized with data from a file.

        Args:
            file_path (str): The path to the file to load data from.

        Returns:
            StringMD5Counter: An instance of the class initialized with the loaded data.
        """
        instance = cls()
        try:
            with open(file_path, 'r') as file:
                instance.md5_count = json.load(file)
        except FileNotFoundError:
            pass  # If file does not exist, return an empty instance
        return instance

    # def draw_histogram(self):
    #     """
    #     Draw a histogram of the counts of string occurrences.
    #     """
    #     counts = list(self.md5_count.values())
    #     plt.figure(figsize=(10, 6))
    #     plt.hist(counts, bins=range(1, max(counts) + 2), edgecolor='black', align='left')
    #     plt.title('Histogram of String Occurrence Counts')
    #     plt.xlabel('Count')
    #     plt.ylabel('Frequency')
    #     plt.xticks(range(1, max(counts) + 1))
    #     plt.grid(axis='y', linestyle='--', alpha=0.7)
    #     plt.show()

    def __repr__(self):
        """
        Return a string representation of the counter.

        Returns:
            str: A string representation of the dictionary containing MD5 hashes and their counts.
        """
        return str(self.md5_count)


