import bisect
from pathlib import Path
import re
from typing import Dict, List, Set, TextIO


class Replacement:
    """

    """

    def __init__(self, file_path: Path, line_number: int, original: str, new: str):
        """

        :param file_path:
        :param line_number:
        :param original:
        :param new:
        """
        self.file_path = file_path
        self.line_number = line_number
        self.original_key = original
        self.new_key = new

    def __str__(self):
        """

        :return:
        """
        return ','.join([str(self.file_path), str(self.line_number), self.original_key, self.new_key])


class SourceDir:
    """

    """

    def __init__(self, abs_path: Path, pattern: str, ignore: List[str]):
        """

        :param abs_path:
        :param pattern:
        :param ignore:
        """
        self.path = abs_path
        self.pattern = pattern
        self.ignore = ignore


class ParserAndReplacer:
    """

    """
    # class variables are shared, so use only one of these classes at a time
    cleaned_file_contents: str
    f: TextIO
    file_name: Path
    line_ending_indexes: List[int]
    potential_calls: List[int]
    replacements: List[Replacement] = []
    original_arg_values: Set[str] = set()

    def __init__(self, dirs: List[SourceDir], function: str, arg_map: Dict[int, Dict[str, str]], verbose: bool):
        """

        :param dirs:
        :param function:
        :param arg_map:
        :param verbose:
        """
        self.verbose = verbose
        self.function_name = function
        self.arg_map = arg_map
        self.dirs = dirs

    def perform_replacements(self):
        """

        :return:
        """
        self._analyze_all_function_calls(just_report=False)
        self._report_all_replacements()
        self._do_replacements()

    def get_current_arg_values(self, arg_num: int):
        """

        :param arg_num:
        :return:
        """
        self._analyze_all_function_calls(just_report=True, arg_num=arg_num)
        self._my_print(f"Original Arg {str(arg_num)} values: ")
        for a in self.original_arg_values:
            self._my_print(f" {a}")

    def _my_print(self, msg: str):
        """

        :param msg:
        :return:
        """
        if self.verbose:
            print(msg)

    def _analyze_all_function_calls(self, just_report: bool, arg_num: int = 0):
        """

        :return:
        """
        # open the main file so that worker functions can write to it
        with open('setup_output_variable_calls.csv', 'w') as self.f:
            for d in self.dirs:
                for p in d.path.glob("**/*"):
                    self._my_print(f"Processing files in {d.path}")
                    if p.is_file() and d.pattern in str(p.name):
                        if any([x in str(p.name) for x in d.ignore]):
                            continue
                        self._do_one_file(p, d.path, just_report, arg_num)

    def _report_all_replacements(self):
        """

        :return:
        """
        with open('replacements.csv', 'w') as f:
            for r in self.replacements:
                f.write(str(r) + '\n')

    def _do_replacements(self):
        """

        :return:
        """
        map_of_replacements = self._get_map_of_replacements()
        for file_path, replacements in map_of_replacements.items():
            print(f"{file_path}")
            lines_with_replacements = self._get_replacement_line_numbers(replacements)
            original_lines = file_path.open().readlines()
            line_number = 0
            with file_path.open('w') as f:
                for line in original_lines:
                    line_number += 1
                    if line_number in lines_with_replacements:
                        for r in replacements:
                            if r.line_number == line_number:
                                line = line.replace(r.original_key, r.new_key)
                    f.write(line)

    def _do_one_file(self, p: Path, root_dir: Path, just_report: bool, arg_num: int):
        """

        :param p:
        :param root_dir:
        :return:
        """
        self.file_name = p.relative_to(root_dir)
        self._my_print(f" Processing file {self.file_name}")
        cleaned_lines = self._get_cleaned_lines(p)
        self.line_ending_indexes = self._get_line_ending_indexes(cleaned_lines)
        self.cleaned_file_contents = ''.join(cleaned_lines)
        self.potential_calls = self._get_call_sites(self.cleaned_file_contents)
        self._my_print(f"  Found {len(self.potential_calls)} {self.function_name} calls in this file")
        self._iterate_over_call_sites(p, just_report, arg_num)

    def _iterate_over_call_sites(self, p: Path, just_report: bool, arg_num: int):
        """

        :return:
        """
        for starting_position in self.potential_calls:
            self._visit_one_call_site(p, starting_position, just_report, arg_num)

    def _visit_one_call_site(self, p: Path, starting_position: int, just_report: bool, arg_num: int):
        """

        :param starting_position:
        :return:
        """
        # start searching after the call opens, set initial parenthesis level to 1
        parenthesis_level = 1
        ending_position = starting_position + 19
        argument_list = []
        current_argument = ''
        function_call_length = 0
        num_args_parsed = 0
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
                    num_args_parsed += 1  # not actually necessary but here for posterity
                    argument_list.append(current_argument.strip())
                    break
            elif new_character == ',' and parenthesis_level == 1:
                this_arg = current_argument.strip()
                num_args_parsed += 1
                current_argument = ''
                # num_args_parsed includes the one we just finished
                # so if we just finished the 3rd argument, num_args_parsed would be 3
                # we will process the argument in the replacement map in a 1 based fashion, so it is exactly this var
                new_arg = this_arg
                if just_report:
                    if num_args_parsed == arg_num:
                        self.original_arg_values.add(this_arg)
                elif num_args_parsed in self.arg_map:
                    if this_arg in self.arg_map[num_args_parsed]:
                        new_arg = self.arg_map[num_args_parsed][this_arg]
                        self.replacements.append(Replacement(p, line_number, this_arg, new_arg))
                    else:
                        raise Exception(
                            f"Argument did not exist in arg_map; index={num_args_parsed}; original_key={this_arg}"
                        )
                argument_list.append(new_arg)
                continue
            current_argument += new_character
        self.f.write(",".join([str(self.file_name), str(line_number)] + argument_list) + '\n')

    @staticmethod
    def _get_cleaned_lines(p: Path):
        """

        :param p:
        :return:
        """
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
    def _get_line_ending_indexes(cleaned_lines: List[str]):
        line_ending_indexes = [0]
        length_counter = 0
        for line in cleaned_lines:
            length_counter += len(line)
            line_ending_indexes.append(length_counter)
        return line_ending_indexes

    def _get_call_sites(self, file_contents: str):
        return [m.start() for m in re.finditer(re.escape(f'{self.function_name}('), file_contents)]

    def _get_map_of_replacements(self) -> Dict[Path, List[Replacement]]:
        d = {}
        for r in self.replacements:
            if r.file_path not in d:
                d[r.file_path] = []
            d[r.file_path].append(r)
        return d

    @staticmethod
    def _get_replacement_line_numbers(replacements: List[Replacement]) -> List[int]:
        lines = []
        for r in replacements:
            lines.append(r.line_number)
        return lines
