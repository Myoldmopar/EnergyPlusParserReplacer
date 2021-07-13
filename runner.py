from pathlib import Path

from parser_replacer.library import ParserAndReplacer, SourceDir

if __name__ == "__main__":
    repo_root = "C:/EnergyPlus/repos/1eplus"
    source_dirs = [
        SourceDir(abs_path=Path(repo_root) / 'src' / 'EnergyPlus', pattern=".cc", ignore=['OutputProcessor.cc']),
        SourceDir(abs_path=Path(repo_root) / 'tst' / 'EnergyPlus' / 'unit', pattern=".unit.cc", ignore=[]),
    ]
    function_name = 'SetupOutputVariable'
    replacement_map = {
        5: {
            "\"system\"": "SomethingFromSystem",
            "\"HVAC\"": "SomethingFromSystem",
            "\"ZONE\"": "SomethingFromSystem",
            "sUpdateFreq": "SomethingFromSystem",
            "FreqString": "SomethingFromSystem",
            "\"Zone\"": "SomethingFromSystem",
            "\"Plant\"": "SomethingFromSystem",
            "\"System\"": "SomethingFromSystem",
            "OUTPUTPROCESSOR::ETIMESTEPTYPE": "TODO: Use special key for keeping original"
            # TODO: use special key to keep original
        },
        6: {
            "\"State\"": "SomethingNew",
            "sAvgOrSum": "SomethingNew",
            "\"Summed\"": "SomethingNew",
            "VarTypeString": "SomethingNew",
            "\"Average\"": "SomethingNew",
            "\"Sum\"": "SomethingNew",
            "\"NonState\"": "SomethingNew",
            "OUTPUTPROCESSOR::EVARIABLETYPE": "Use Original"
        }
    }
    parser = ParserAndReplacer(
        source_dirs,
        function_name,
        replacement_map,
        verbose=True
    )
    # parser.get_current_arg_values(6)
    parser.perform_replacements()
