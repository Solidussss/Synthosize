#pragma once
#include <JuceHeader.h>
#include <atomic>

// Audio is passed through unmodified. The audio thread only copies host time
// into atomics; video encoding and networking must never run here.
class SynthosizeProcessor final : public juce::AudioProcessor
{
public:
    SynthosizeProcessor();
    const juce::String getName() const override { return "Synthosize Visual Studio"; }
    void prepareToPlay(double, int) override {}
    void releaseResources() override {}
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override { return true; }
    double getTailLengthSeconds() const override { return 0.0; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override {}
    void setStateInformation(const void*, int) override {}

    std::atomic<double> hostBpm { 120.0 };
    std::atomic<double> hostPpq { 0.0 };
    std::atomic<bool> hostPlaying { false };
    std::atomic<bool> hostAvailable { false };

private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(SynthosizeProcessor)
};
