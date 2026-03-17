# Mirror — Demo Script

**Target duration:** 3 minutes  
**Format:** Live demo with one person presenting, two running the laptop

---

## Setup (before presentation)

- Pre-load a worksheet fixture (Spanish subjunctive lesson, 8 items)
- Have the Teacher Panel open on screen
- Have a demo student account ready ("Ana García")
- Confirm Agora mic is working
- Have the backup video ready if anything breaks

---

## The Script

### [0:00–0:25] Hook

> "Every language lesson ends with the same problem: the student walks out the door, and 80% of what they just learned fades before the next session. Homework is static. Worksheets don't adapt. And teachers have no idea what actually stuck.
>
> This is Mirror."

*[Screen shows the Mirror logo/landing screen]*

---

### [0:25–0:55] Teacher flow

> "After a lesson, the teacher — in 60 seconds — uploads their worksheet, tags what they covered, and leaves a quick note."

*[Demo: drag-drop PDF worksheet → parsed exercise items appear in real time]*

> "Our parser uses GPT-4o to extract every vocabulary item, every conjugation target, every exercise prompt — structured and ready."

*[Demo: teacher types/selects "subjunctive mood", checks "conjugation" + "speaking", sets 8s timer, types: "She kept mixing up ser and estar — focus there first"]*

> "That note becomes intent. The AI reads it."

---

### [1:00–1:35] Student flow — avatar activates

*[Switch to student view — Anam avatar appears]*

> "The student opens Mirror after their lesson. The avatar already knows what happened."

*[Avatar speaks]:* *"Hi Ana! Great session today. You tackled subjunctive mood — let's make sure it actually sticks. We've got 10 minutes. Ready?"*

> "The avatar runs the first exercise."

*[Avatar]:* *"Conjugate 'querer' in the subjunctive for 'ella'. You have 8 seconds."*

*[Timer ring counts down — student answers via mic: "quiera"]*

*[Thymia scores it — green flash, avatar responds]:* *"Perfect. Nice and fast too."*

---

### [1:35–2:05] RL + timer in action

> "Here's where it gets interesting. The student hesitates on the next one."

*[Avatar]:* *"Use 'quiera' in a sentence about ordering food. 15 seconds."*

*[Timer runs down to 50% — subtle pulse. Runs to 0.]*

*[Avatar, patiently]:* *"Think about a restaurant scenario... maybe something you'd say to a waiter?"*

*[Student responds]: "Quiero que el camarero... quiera... traernos la carta."*

*[Score: partial. RL engine notes: this item needs re-queuing in a different format.]*

> "The RL engine saw that hesitation. It'll come back — in a different format, with a tighter timer, before this session ends."

---

### [2:05–2:35] Dashboard + teacher debrief

*[Session ends — dashboard appears]*

> "After 10 minutes, Mirror surfaces what actually happened."

*[Show: fluency score 71% → up from 64% last session. Hesitation heatmap — 'subjunctive of irregular verbs' is the red zone. 7/10 exercises completed.]*

> "And the teacher gets a debrief before the next lesson."

*[Switch to teacher view]:* *"Ana completed 7 of 10 exercises. Subjunctive of 'querer' and 'poder' still need work. Suggest opening next lesson with a 5-minute review."*

---

### [2:35–3:00] Close

> "Mirror uses all five partner technologies together — Agora for real-time audio, Thymia for speech scoring, OpenAI for reasoning, Anam for the human-feeling delivery, and AWS for the learner state that persists across every session.
>
> The teacher sets the intent. The RL engine optimizes the delivery. And the student actually remembers what they learned.
>
> This is Mirror."

---

## Backup plan

If any live API fails during the demo, switch to the pre-recorded video at `scripts/demo_recording.mp4`. Keep it loaded in a browser tab the entire time.
