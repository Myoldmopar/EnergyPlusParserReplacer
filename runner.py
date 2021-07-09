import bisect
from pathlib import Path
import re

RepoRoot = "C:/EnergyPlus/repos/3eplus"


class Replacement:
    def __init__(self, file_path, line_number, original, new):
        self.file_path = file_path
        self.line_number = line_number
        self.original_key = original
        self.new_key = new


replacements = []


class ParserAndReplacer:

    def __init__(self, repository_path: str, verbose: bool = False):
        self.verbose = verbose
        repo_p = Path(repository_path)
        self.energy_plus_dir = repo_p / 'src' / 'EnergyPlus'
        self.f = None  # will be a file handle

    def my_print(self, msg: str):
        if self.verbose:
            print(msg)

    def do(self):
        with open('C:/tmp/hello.csv', 'w') as self.f:
            self.my_print(f"Processing files in {self.energy_plus_dir}")
            for p in self.energy_plus_dir.iterdir():
                if p.is_file() and str(p.name).endswith(".cc"):
                    if "OutputProcessor.cc" in str(p.name):
                        continue
                    self.do_one_file(p)

    @staticmethod
    def get_cleaned_lines(p: Path):
        file_lines = p.open(encoding='utf-8', errors='ignore').readlines()
        cleaned_lines = []
        for li in file_lines:
            remaining_line = li
            if '//' in li:
                index = li.index('//')
                remaining_line = li[:index]
            if remaining_line == "":
                cleaned_lines.append('\n')
            else:
                cleaned_lines.append(remaining_line)
        return cleaned_lines

    def do_one_file(self, p: Path):
        file_name = p.relative_to(self.energy_plus_dir)
        self.my_print(f" Processing file {file_name}")
        cleaned_lines = self.get_cleaned_lines(p)
        line_ending_indexes = [0]
        length_counter = 0
        for line in cleaned_lines:
            length_counter += len(line)  # TODO: Do we need a +1 for a \n? -- I don't think so
            line_ending_indexes.append(length_counter)
        file_contents = ''.join(cleaned_lines)
        potential_calls = [m.start() for m in re.finditer(re.escape('SetupOutputVariable('), file_contents)]
        self.my_print(f"  Found {len(potential_calls)} SetupOutputVariable calls in this file")
        for starting_position in potential_calls:
            # start searching after the call opens, set initial level to 1
            parenthesis_level = 1
            line_number = bisect.bisect(line_ending_indexes, starting_position)
            ending_position = starting_position + 19
            argument_list = []
            current_argument = ''
            function_call_length = 0
            while True:
                ending_position += 1
                function_call_length += 1
                new_character = file_contents[ending_position]
                if new_character == '(':
                    parenthesis_level += 1
                elif new_character == ')':
                    parenthesis_level -= 1
                    if parenthesis_level == 0:
                        argument_list.append(current_argument.strip())
                        break
                elif new_character == ',' and parenthesis_level == 1:
                    argument_list.append(current_argument.strip())
                    if len(argument_list) == 5:
                        arg4 = argument_list[4].upper()
                        if arg4 == "\"PLANT\"":
                            new_arg = "SOMETHING_FROM_PLANT"
                        elif arg4 == "\"SYSTEM\"":
                            new_arg = "SOMETHING_FROM_SYSTEM"
                        elif arg4 == "\"ZONE\"":
                            new_arg = "SOMETHING_FROM_ZONE"
                        elif arg4 == "\"HVAC\"":
                            new_arg = "SOMETHING_FROM_HVAC"
                        elif arg4 == "SUPDATEFREQ":
                            new_arg = "SOMETHING_FROM_SUPDATEFREQ"  # special case for some plugin author idiot
                        elif arg4 == "FREQSTRING":
                            new_arg = "SOMETHING_FROM_FREQSTRING"  # special case for some ERL author
                        else:
                            raise Exception("4: " + argument_list[4])
                        self.my_print(
                            ','.join([str(p.absolute()), str(line_number), current_argument.strip(), new_arg]))
                    elif len(argument_list) == 6:
                        if argument_list[5].upper() == "\"AVERAGE\"":
                            ...
                        elif argument_list[5].upper() == "\"SUM\"":
                            ...
                        elif argument_list[5].upper() == "\"SUMMED\"":
                            ...
                        elif argument_list[5].upper() == "\"STATE\"":
                            ...
                        elif argument_list[5].upper() == "\"NONSTATE\"":
                            ...
                        elif argument_list[5].upper() == "SAVGORSUM":
                            ...  # special case for some plugin author idiot
                        elif argument_list[5].upper() == "VARTYPESTRING":
                            ...  # special case for some ERL author
                        else:
                            raise Exception("5: " + argument_list[5])
                    current_argument = ''
                    continue
                current_argument += new_character
            self.f.write(",".join([str(file_name), str(line_number)] + argument_list) + '\n')


if __name__ == "__main__":
    ParserAndReplacer(RepoRoot, verbose=True).do()
