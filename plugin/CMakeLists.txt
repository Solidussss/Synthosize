cmake_minimum_required(VERSION 3.22)
project(SynthosizeFLPlugin VERSION 0.1.0 LANGUAGES C CXX)

include(FetchContent)
FetchContent_Declare(juce
  GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
  GIT_TAG 8.0.10
  GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(juce)

juce_add_plugin(SynthosizeFL
  COMPANY_NAME "Synthosize"
  BUNDLE_ID "com.synthosize.visualstudio"
  PLUGIN_MANUFACTURER_CODE Synt
  PLUGIN_CODE SyVs
  FORMATS VST3
  PRODUCT_NAME "Synthosize Visual Studio"
  IS_SYNTH FALSE
  NEEDS_MIDI_INPUT FALSE
  NEEDS_MIDI_OUTPUT FALSE
  IS_MIDI_EFFECT FALSE
  COPY_PLUGIN_AFTER_BUILD FALSE)

juce_generate_juce_header(SynthosizeFL)

target_sources(SynthosizeFL PRIVATE
  Source/PluginProcessor.cpp
  Source/PluginEditor.cpp)
target_include_directories(SynthosizeFL PRIVATE Source)
target_compile_features(SynthosizeFL PRIVATE cxx_std_17)
target_compile_definitions(SynthosizeFL PUBLIC
  JUCE_WEB_BROWSER=0
  JUCE_USE_CURL=0
  JUCE_VST3_CAN_REPLACE_VST2=0)
target_link_libraries(SynthosizeFL PRIVATE
  juce::juce_audio_utils
  juce::juce_gui_extra
  juce::juce_recommended_config_flags
  juce::juce_recommended_warning_flags)
