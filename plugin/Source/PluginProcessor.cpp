#include "PluginProcessor.h"
#include "PluginEditor.h"

SynthosizeProcessor::SynthosizeProcessor()
    : AudioProcessor(BusesProperties()
        .withInput("Input", juce::AudioChannelSet::stereo(), true)
        .withOutput("Output", juce::AudioChannelSet::stereo(), true))
{
}

void SynthosizeProcessor::processBlock(juce::AudioBuffer<float>& audio, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    // Do not modify the source beat or project audio.
    if (auto* head = getPlayHead())
    {
        if (auto position = head->getPosition())
        {
            hostAvailable.store(true, std::memory_order_relaxed);
            if (auto bpm = position->getBpm())
                hostBpm.store(*bpm, std::memory_order_relaxed);
            if (auto ppq = position->getPpqPosition())
                hostPpq.store(*ppq, std::memory_order_relaxed);
            hostPlaying.store(position->getIsPlaying(), std::memory_order_relaxed);
            return;
        }
    }
    hostAvailable.store(false, std::memory_order_relaxed);
    juce::ignoreUnused(audio);
}

juce::AudioProcessorEditor* SynthosizeProcessor::createEditor()
{
    return new SynthosizeEditor(*this);
}

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new SynthosizeProcessor();
}
