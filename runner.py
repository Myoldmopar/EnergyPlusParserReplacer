from pathlib import Path

from parser_replacer.library import ParserAndReplacer, SourceDir

# TODO: Use a special key in the replacement maps for "keep the original item here"

if __name__ == "__main__":
    repo_root = "/eplus/repos/7eplus"
    source_dirs = [
        SourceDir(abs_path=Path(repo_root) / 'src' / 'EnergyPlus', pattern=".cc", ignore=['OutputProcessor.cc']),
        SourceDir(abs_path=Path(repo_root) / 'tst' / 'EnergyPlus' / 'unit', pattern=".unit.cc", ignore=[]),
    ]
    function_name = 'SetupOutputVariable'
    replacement_map = {
        5: {
            "\"system\"": "OutputProcessor::SOVTimeStepType::System",
            "\"HVAC\"": "OutputProcessor::SOVTimeStepType::HVAC",
            "\"ZONE\"": "OutputProcessor::SOVTimeStepType::Zone",
            "\"Zone\"": "OutputProcessor::SOVTimeStepType::Zone",
            "\"Plant\"": "OutputProcessor::SOVTimeStepType::Plant",
            "\"System\"": "OutputProcessor::SOVTimeStepType::System",
            "sUpdateFreq": "OutputProcessor::SOVTimeStepType::SOMETHING_FROM_SUPDATEFREQ",
            "FreqString": "OutputProcessor::SOVTimeStepType::SOMETHING_FROM_FREQSTRING",
        },
        6: {
            "\"State\"": "OutputProcessor::SOVStoreType::State",
            "\"Summed\"": "OutputProcessor::SOVStoreType::Summed",
            "\"Average\"": "OutputProcessor::SOVStoreType::Average",
            "\"Sum\"": "OutputProcessor::SOVStoreType::Summed",
            "\"NonState\"": "OutputProcessor::SOVStoreType::NonState",
            "sAvgOrSum": "OutputProcessor::SOVStoreType::SOMETHING_FROM_SAVGORSUM",
            "VarTypeString": "OutputProcessor::SOVStoreType::SOMETHING_FROM_VARTYPESTRING",
        }
    }
    parser = ParserAndReplacer(
        source_dirs,
        function_name,
        replacement_map,
        verbose=True
    )
    # parser.get_current_arg_values(5)
    parser.perform_replacements()
