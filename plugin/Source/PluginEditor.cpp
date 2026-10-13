#include "PluginEditor.h"

SynthosizeEditor::SynthosizeEditor(SynthosizeProcessor& owner)
    : AudioProcessorEditor(&owner), processor(owner)
{
    setSize(540, 250);
    title.setText("SYNTHOSIZE  /  VISUAL STUDIO", juce::dontSendNotification);
    title.setFont(juce::FontOptions(22.0f, juce::Font::bold));
    title.setColour(juce::Label::textColourId, juce::Colours::white);
    addAndMakeVisible(title);
    transport.setColour(juce::Label::textColourId, juce::Colours::cyan);
    transport.setFont(juce::FontOptions(18.0f));
    addAndMakeVisible(transport);
    explanation.setText("VST3 foundation: reads FL Studio tempo / transport, passes audio through.\n"
                        "Scene editor and export bridge are the next milestone.",
                        juce::dontSendNotification);
    explanation.setColour(juce::Label::textColourId, juce::Colours::lightgrey);
    explanation.setJustificationType(juce::Justification::centredLeft);
    addAndMakeVisible(explanation);
    startTimerHz(12);
    timerCallback();
}

void SynthosizeEditor::paint(juce::Graphics& g)
{
    g.fillAll(juce::Colour::fromRGB(13, 15, 25));
    g.setColour(juce::Colour::fromRGB(26, 31, 54));
    g.fillRoundedRectangle(getLocalBounds().toFloat().reduced(12.0f), 13.0f);
}

void SynthosizeEditor::resized()
{
    auto area = getLocalBounds().reduced(30);
    title.setBounds(area.removeFromTop(46));
    area.removeFromTop(8);
    transport.setBounds(area.removeFromTop(55));
    explanation.setBounds(area.removeFromTop(74));
}

void SynthosizeEditor::timerCallback()
{
    if (!processor.hostAvailable.load(std::memory_order_relaxed))
    {
        transport.setText("Waiting for host transport...", juce::dontSendNotification);
        return;
    }
    const auto bpm = processor.hostBpm.load(std::memory_order_relaxed);
    const auto ppq = processor.hostPpq.load(std::memory_order_relaxed);
    const bool playing = processor.hostPlaying.load(std::memory_order_relaxed);
    // Send host timing to the local desktop editor. Never do network I/O on
    // FL Studio's realtime audio thread; this timer runs on the UI thread.
    // Only loopback transport metadata is sent, never audio or media files.
    const auto state = juce::String::formatted(
        "{\"bpm\":%.6f,\"ppq\":%.6f,\"playing\":%s}",
        bpm, ppq, playing ? "true" : "false");
    transportSocket.write("127.0.0.1", 48383, state.toRawUTF8(),
                          static_cast<int>(state.getNumBytesAsUTF8()));

    transport.setText(juce::String(bpm, 1) + " BPM   |   Beat " +
        juce::String(ppq, 2) + "   |   " + (playing ? "PLAYING" : "STOPPED"),
        juce::dontSendNotification);
}
