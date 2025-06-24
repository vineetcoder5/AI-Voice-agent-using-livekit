# ☎️ AI-Voice-agent-using-livekit

Setup
---

## 📆 Clone the Repository

```bash
git clone https://github.com/vineetcoder5/riverline-challenge.git
cd riverline-challenge
```

---

## 🛠️ STEP 1: Download LiveKit Server Binary

1. Visit the [LiveKit GitHub Releases](https://github.com/livekit/livekit-server/releases) page.
2. Download the appropriate binary for **Windows**:

   * Example: `livekit-windows-amd64.exe`
3. Rename it to `livekit.exe`.

### Optional: Add to PATH

* Move `livekit.exe` to a directory like `C:\tools\livekit`.
* Add the directory to your system `PATH`:

  * Search for `Environment Variables` in Start Menu.
  * Edit System Variables → Path → Add: `C:\tools\livekit`

---

## 📋 STEP 2: Install Dependencies

Install Python dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🎯 Running the Voice Agent

### 🔧 Configure `.env.local`

Go inside the `challenge_1` folder and create a `.env.local` file:

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id
GOOGLE_API_KEY=your_gemini_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
CARTESIA_API_KEY=your_cartesia_api_key
```

---

## ☎️ STEP 3: Create SIP Trunk on Twilio

1. Watch this YouTube guide:
   📺 [Twilio SIP Setup (17:53–27:00)](https://www.youtube.com/watch?v=1PA1QoRhddw&t=1073s)
2. Update `outbound-trunk.json` in `challenge_1` folder with Twilio SIP details:

```json
{
  "name": "YourTrunkName",
  "address": "your-domain.pstn.twilio.com",
  "numbers": ["+1234567890"],
  "auth_username": "your_username",
  "auth_password": "your_password"
}
```

3. Generate the SIP Outbound Trunk ID:

```bash
lk sip outbound create outbound-trunk.json
```

> Copy the output ID and paste it in `.env.local` as `SIP_OUTBOUND_TRUNK_ID`.

---

## ▶️ STEP 4: Run the Voice Agent

Run the voice agent by executing:

```bash
python agent.py dev
```

This starts the worker process.

---

## 📞 STEP 5: Trigger a Call

In a new terminal, run:

```bash
lk dispatch create --new-room --agent-name outbound-caller --metadata "{\"phone_number\": \"+YourPhoneNumber\"}"
```

## ✅ Success

Your phone should ring, and the AI voice agent will respond to your input.

---

## 📌 Notes

* Make sure all API keys are active and valid.
* Check the terminal logs for errors if something goes wrong.
* This guide assumes you're using **Windows OS**.

---
