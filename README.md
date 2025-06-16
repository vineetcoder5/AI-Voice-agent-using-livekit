🚀 Riverline Challenge – Voice Agent Setup
This guide walks you through the process of setting up and running the voice agent for Challenge_1 using LiveKit and Twilio SIP Trunking.

📦 Clone the Repository
bash
Copy
Edit
git clone https://github.com/your-repo/riverline-challenge.git
cd riverline-challenge
🛠️ STEP 1: Download LiveKit Server Binary
Visit the LiveKit GitHub Releases page.

Download the appropriate Windows binary (e.g., livekit-windows-amd64.exe).

Rename it to livekit.exe.

(Optional) Move it to a system PATH directory (e.g., C:\tools\livekit).

To add to PATH:

Search for Environment Variables in Start Menu.

Go to System Variables > Path and click Edit.

Add: C:\tools\livekit

📚 STEP 2: Install Python Dependencies
Navigate to the root of the project and run:

bash
Copy
Edit
pip install -r requirements.txt
🎯 Challenge 1 – Running the Voice Agent
🔑 Set Up .env.local
Inside the challenge_1 folder, create a .env.local file with the following:

env
Copy
Edit
LIVEKIT_URL=<Your LiveKit URL>
LIVEKIT_API_KEY=<Your LiveKit API Key>
LIVEKIT_API_SECRET=<Your LiveKit API Secret>
SIP_OUTBOUND_TRUNK_ID=<Generated in Step 2>
GOOGLE_API_KEY=<Your Gemini API Key>
DEEPGRAM_API_KEY=<Your Deepgram API Key>
CARTESIA_API_KEY=<Your Cartesia API Key>
☎️ STEP 2: Create SIP Trunk in Twilio
Watch this YouTube guide (Time: 17:53–27:00) to create your SIP trunk in Twilio.

Fill in the outbound-trunk.json file in challenge_1 with your Twilio SIP trunk details:

json
Copy
Edit
{
  "name": "YourTrunkName",
  "address": "your-domain.pstn.twilio.com",
  "numbers": ["+1234567890"],
  "auth_username": "your_username",
  "auth_password": "your_password"
}
Generate your SIP Outbound Trunk ID:

bash
Copy
Edit
lk sip outbound create outbound-trunk.json
Copy the generated ID and paste it into SIP_OUTBOUND_TRUNK_ID in .env.local.

▶️ STEP 3: Run the Agent
Navigate to the challenge_1 directory and run the agent:

bash
Copy
Edit
python agent.py dev
This creates a worker that listens for room creation.

📞 STEP 4: Trigger the Outbound Call
In a new terminal, navigate to challenge_1 and run:

bash
Copy
Edit
lk dispatch create --new-room --agent-name outbound-caller --metadata "{\"phone_number\": \"+YourPhoneNumber\"}"
Your phone should ring, and you'll be able to interact with the voice agent 🎤.

✅ You're Done!
If all steps are correct, your AI voice agent should call you and start interacting. For troubleshooting, check logs in the console and ensure all API keys are valid.
