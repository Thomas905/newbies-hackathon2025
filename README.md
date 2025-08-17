# NewBies Hackathon UQCS 2025
# PVZ: Wrist in Peas

## 🎮 What is this project?

**PVZ: Wrist in Peas** is a wrist-controlled motion game — a vertical scrolling shooter in the style of *space shooters*, but with a playful twist: it's themed after **Plants vs Zombies**.

Each round lasts about **2 minutes**, designed for light wrist activity — perfect as a quick break from typing or gaming marathons.

---

## 🕹 How to Play

You are **a humble zombie craving brains**, shambling up the lawn. Just like in the original *Plants vs Zombies*, plants form layered defenses.  
Your goal: **survive** the plant barrage and reach the end of the lawn to enjoy a fresh, delicious brain! 🧠

### Controls

- **Setup:**  
  Extend your right arm toward your PC screen, **back of the hand facing up**, so your webcam can capture your palm movements.
  
- **Move Right:**  
  Rotate your palm **clockwise** by 90°.

- **Move Left:**  
  Rotate your palm **counterclockwise** by a smaller angle.

- **Move Up / Down:**  
  Flex or extend your wrist.

- **(Optional) Special Skill:**  
  If stamina allows, we plan to add a custom gesture for skill activation  
  *(e.g., middle finger salute — though more likely a simple fist ✊)*.

---

## 💡 Health Note
The motion control is designed for **short bursts of gentle wrist activity**, helping keep joints mobile and reducing stiffness from prolonged computer use.

---

## 🛠 Tech Stack(TBD)
- **Platform:** Webapp? 
- **Control:** Webcam hand tracking (MediaPipe Hands)
- **Style:** Parody of *Plants vs Zombies* with arcade space shooter mechanics

---

## 📜 Credits
Made during a hackathon, with love, laughs, and slightly sore wrists.

# 关于 rebase 和 merge 的选择建议

- **如果你的更改比远程更重要**，推荐使用 `rebase`，这样可以让你的提交排在远程提交之后，历史更线性，方便 review 和后续 push。
- 具体做法：
  1. 先拉取远程分支并 rebase 到你的本地分支：
     ```
     git pull --rebase origin fix/deadbug
     ```
  2. 如果有冲突，解决冲突后继续 rebase：
     ```
     git rebase --continue
     ```
  3. rebase 完成后再 push（如果远程已有你的旧提交，需要强推）：
     ```
     git push --force-with-lease
     ```

- **merge** 会保留两边的历史，产生一次合并提交。如果你希望保留所有历史（比如团队协作复杂、需要追溯每个人的分支），可以用 merge：
  ```
  git pull --no-rebase origin fix/deadbug
  ```

- **总结**：  
  - 你想让你的更改“压”在远程之上、历史更干净，选 `rebase`。
  - 你想保留所有分支的历史，选 `merge`。

> ⚠️ 注意：rebase 后强推会覆盖远程分支历史，请确保团队成员知情。
