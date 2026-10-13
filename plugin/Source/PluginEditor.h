#pragma once
#include "PluginProcessor.h"

class SynthosizeEditor final : public juce::AudioProcessorEditor, private juce::Timer
{
public:
    explicit SynthosizeEditor(SynthosizeProcessor&);
    void paint(juce::Graphics&) override;
    void resized() override;

private:
    void timerCallback() override;
    SynthosizeProcessor& processor;
    juce::Label title;
    juce::Label transport;
    juce::Label explanation;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SynthosizeEditor)
};
