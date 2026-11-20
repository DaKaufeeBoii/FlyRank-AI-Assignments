# CogniFlow Incident Intelligence — Build Log (BUILDLOG.md)
**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Track:** General AI Fluency Capstone (Impact Project)  

---

## 1. Where AI Assisted the Build
- **Log Parsing Regular Expressions:** AI helped craft efficient pattern matching for typical distributed log signatures (connection timeouts, deadlock identifiers, JWT expiry patterns).
- **Executive Dashboard Styling:** Generated the self-contained dark-mode CSS theme for `output/dashboard.html` adhering to modern developer tooling aesthetics.

---

## 2. Where AI Was Wrong & Required Human Engineering Correction

### Issue 1: Over-Reliance on Hallucinated Incident Details
* **The AI's Mistake:**  
  Early prompt iterations caused the model to hallucinate specific server hostnames and IPs not present in the input logs (e.g., claiming `ip-10-0-4-12.ec2.internal was restarted`).
* **My Correction:**  
  I enforced strict Pydantic schema validation requiring provenance extraction: only facts directly observed in the log stream may be referenced in the root-cause summary.

### Issue 2: Fluffy, Passive Customer Communication Drafts
* **The AI's Mistake:**  
  Initial AI-generated customer updates were laden with passive corporate apologies: *"We apologize for any inconvenience caused while we continuously optimize our synergies..."*
* **My Correction:**  
  Injected my **Voice Card** standing instruction (*"Direct, plain, technical, pragmatic, zero buzzwords"*). The updated drafts state exactly what happened, what is unaffected, and when the next status update will arrive.

---

## 3. Defense Verification
I can explain every component of this project:
- The economic modeling behind the 560 engineering hours saved.
- The distinction between automated drafting and human verification gates.
- How the system guarantees zero data leakage between internal root causes and external customer updates.
