import bisect
from pathlib import Path
import re
from typing import List, TextIO

RepoRoot = "C:/EnergyPlus/repos/3eplus"


class Replacement:
    def __init__(self, file_path: Path, line_number: int, original: str, new: str):
        self.file_path = file_path
        self.line_number = line_number
        self.original_key = original
        self.new_key = new

    def __str__(self):
        return ','.join([str(self.file_path), str(self.line_number), self.original_key, self.new_key])


class ParserAndReplacer:
    # class variables are shared, so use only one of these classes at a time
    cleaned_file_contents: str
    f: TextIO
    file_name: Path
    line_ending_indexes: List[int]
    potential_calls: List[int]
    replacements: List[Replacement] = []

    def __init__(self, repository_path: str, verbose: bool = False):
        self.verbose = verbose
        self.energy_plus_dir = Path(repository_path) / 'src' / 'EnergyPlus'

    def my_print(self, msg: str):
        if self.verbose:
            print(msg)

    def do_one_repository(self):
        # open the main file so that worker functions can write to it
        with open('C:/tmp/setup_output_variable_calls.csv', 'w') as self.f:
            self.my_print(f"Processing files in {self.energy_plus_dir}")
            for p in self.energy_plus_dir.iterdir():
                if p.is_file() and str(p.name).endswith(".cc"):
                    if "OutputProcessor.cc" in str(p.name):
                        continue
                    self.do_one_file(p)
        with open('C:/tmp/replacements.csv', 'w') as f:
            for r in self.replacements:
                f.write(str(r) + '\n')

    def do_one_file(self, p: Path):
        self.file_name = p.relative_to(self.energy_plus_dir)
        self.my_print(f" Processing file {self.file_name}")
        cleaned_lines = self.get_cleaned_lines(p)
        self.line_ending_indexes = self.get_line_ending_indexes(cleaned_lines)
        self.cleaned_file_contents = ''.join(cleaned_lines)
        self.potential_calls = self.get_call_sites(self.cleaned_file_contents)
        self.my_print(f"  Found {len(self.potential_calls)} SetupOutputVariable calls in this file")
        self.iterate_over_call_sites(p)

    def iterate_over_call_sites(self, p: Path):
        for starting_position in self.potential_calls:
            self.visit_one_call_site(p, starting_position)

    def visit_one_call_site(self, p: Path, starting_position: int):
        # start searching after the call opens, set initial parenthesis level to 1
        parenthesis_level = 1
        ending_position = starting_position + 19
        argument_list = []
        current_argument = ''
        function_call_length = 0
        while True:
            ending_position += 1
            line_number = bisect.bisect(self.line_ending_indexes, ending_position)
            function_call_length += 1
            new_character = self.cleaned_file_contents[ending_position]
            if new_character == '(':
                parenthesis_level += 1
            elif new_character == ')':
                parenthesis_level -= 1
                if parenthesis_level == 0:
                    argument_list.append(current_argument.strip())
                    break
            elif new_character == ',' and parenthesis_level == 1:
                this_arg = current_argument.strip()
                current_argument = ''
                if len(argument_list) in [0, 1, 2, 3]:
                    new_arg = this_arg
                elif len(argument_list) == 4:
                    new_arg = self.get_new_arg4(this_arg)
                    self.replacements.append(Replacement(p, line_number, this_arg, new_arg))
                elif len(argument_list) == 5:
                    new_arg = self.get_new_arg5(this_arg)
                    self.replacements.append(Replacement(p, line_number, this_arg, new_arg))
                else:
                    new_arg = this_arg
                argument_list.append(new_arg)
                continue
            current_argument += new_character
        self.f.write(",".join([str(self.file_name), str(line_number)] + argument_list) + '\n')

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

    @staticmethod
    def get_line_ending_indexes(cleaned_lines: List[str]):
        line_ending_indexes = [0]
        length_counter = 0
        for line in cleaned_lines:
            length_counter += len(line)  # TODO: Do we need a +1 for a \n? -- I don't think so
            line_ending_indexes.append(length_counter)
        return line_ending_indexes

    @staticmethod
    def get_call_sites(file_contents: str):
        return [m.start() for m in re.finditer(re.escape('SetupOutputVariable('), file_contents)]

    @staticmethod
    def get_new_arg4(original_arg: str) -> str:
        arg4 = original_arg.upper()
        if arg4 == "\"PLANT\"":
            return "SOMETHING_FROM_PLANT"
        elif arg4 == "\"SYSTEM\"":
            return "SOMETHING_FROM_SYSTEM"
        elif arg4 == "\"ZONE\"":
            return "SOMETHING_FROM_ZONE"
        elif arg4 == "\"HVAC\"":
            return "SOMETHING_FROM_HVAC"
        elif arg4 == "SUPDATEFREQ":
            return "SOMETHING_FROM_SUPDATEFREQ"  # special case for some plugin author idiot
        elif arg4 == "FREQSTRING":
            return "SOMETHING_FROM_FREQSTRING"  # special case for some ERL author
        else:
            raise Exception("4: " + original_arg)

    @staticmethod
    def get_new_arg5(original_arg: str) -> str:
        arg5 = original_arg.upper()
        if arg5 == "\"AVERAGE\"":
            return "SOMETHING_FROM_AVERAGE"
        elif arg5 == "\"SUM\"":
            return "SOMETHING_FROM_SUM"
        elif arg5 == "\"SUMMED\"":
            return "SOMETHING_FROM_SUMMED"
        elif arg5 == "\"STATE\"":
            return "SOMETHING_FROM_STATE"
        elif arg5 == "\"NONSTATE\"":
            return "SOMETHING_FROM_NONSTATE"
        elif arg5 == "SAVGORSUM":
            return "SOMETHING_FROM_SAVGORSUM"  # special case for some plugin author idiot
        elif arg5 == "VARTYPESTRING":
            return "SOMETHING_FROM_VARTYPESTRING"  # special case for some ERL author
        else:
            raise Exception("5: " + original_arg)


if __name__ == "__main__":
    ParserAndReplacer(RepoRoot, verbose=True).do_one_repository()
