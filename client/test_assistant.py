from openvoice_assistant import OpenVoiceAssistant

def main():
    print("Starting OpenVoice Assistant...")
    print("Say 'hey jarvis' to activate the assistant")
    print("Press Ctrl+C to stop")
    
    assistant = OpenVoiceAssistant()
    try:
        assistant.start()
    except KeyboardInterrupt:
        print("\nStopping assistant...")
        assistant.stop()

if __name__ == "__main__":
    main() 