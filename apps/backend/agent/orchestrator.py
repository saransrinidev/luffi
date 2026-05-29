"""
Agent Orchestrator — Connects all layers.

Flow:
1. Intent Layer → extract structured intent
2. Template Engine → try deterministic execution
3. If no template → UI Layer + Decision Layer → LLM picks from candidates
4. Execution Layer → run actions
5. Verification Layer → confirm success
6. Log everything for observability
"""
import logging
import time
from datetime import datetime

from agent.intent_layer import IntentLayer, Intent
from agent.template_engine import TemplateEngine, ActionStep
from agent.ui_layer import UILayer
from agent.decision_layer import DecisionLayer
from agent.execution_layer import ExecutionLayer
from agent.verification_layer import VerificationLayer
from services.status_bar_service import StatusBarService

logger = logging.getLogger(__name__)


class RunLog:
    """Observability log for a single agent run."""

    def __init__(self, command: str):
        self.command = command
        self.start_time = datetime.now()
        self.entries: list[dict] = []

    def log(self, layer: str, event: str, data: dict = None):
        entry = {
            "time": (datetime.now() - self.start_time).total_seconds(),
            "layer": layer,
            "event": event,
            "data": data or {},
        }
        self.entries.append(entry)
        logger.info(f"[{layer}] {event} {data or ''}")

    def summary(self) -> str:
        lines = [f"Command: {self.command}"]
        for e in self.entries:
            lines.append(f"  [{e['time']:.1f}s] {e['layer']}: {e['event']}")
        return "\n".join(lines)


class AgentOrchestrator:
    """Main agent that coordinates all layers."""

    def __init__(self):
        self.intent_layer = IntentLayer()
        self.template_engine = TemplateEngine()
        self.ui_layer = UILayer()
        self.decision_layer = DecisionLayer()
        self.execution_layer = ExecutionLayer()
        self.verification_layer = VerificationLayer()

    def run(self, command: str) -> str:
        """Execute a user command through the layered pipeline."""
        run_log = RunLog(command)
        StatusBarService.show(f"🤖 {command[:40]}")

        # === Layer 1: Intent ===
        StatusBarService.show("📝 Understanding...")
        intent = self.intent_layer.extract(command)
        run_log.log("intent", str(intent))
        print(f"   📝 Intent: {intent}")

        # === Layer 2: Template Match ===
        StatusBarService.show("🔍 Matching template...")
        template_result = self.template_engine.match(intent)

        if template_result and template_result.is_confident:
            # Template found — execute deterministically (no LLM needed!)
            run_log.log("template", "matched", {
                "confidence": template_result.confidence,
                "steps": len(template_result.steps),
            })
            print(f"   ⚡ Template matched ({template_result.confidence:.0%} confidence)")

            result = self._execute_template(template_result, run_log)
            StatusBarService.hide()
            return result

        # === No template — use UI perception + LLM decision ===
        run_log.log("template", "no_match")
        print("   🔄 No template — using UI perception")

        result = self._execute_with_perception(intent, run_log)
        StatusBarService.hide()
        return result

    def _execute_template(self, template_result, run_log: RunLog) -> str:
        """Execute a template's action sequence."""
        results = []

        def on_step(i, step):
            msg = f"▶ Step {i+1}: {step}"
            StatusBarService.show(msg)
            print(f"   {msg}")
            run_log.log("execution", str(step))

        exec_results = self.execution_layer.execute_sequence(
            template_result.steps, on_step=on_step
        )

        for r in exec_results:
            results.append(str(r))

        # Verify last meaningful action
        last_step = template_result.steps[-1]
        if last_step.action == "done":
            msg = last_step.params.get("message", "Done")
            run_log.log("done", msg)
            return f"✅ {msg}\n\n" + "\n".join(results)

        return "\n".join(results)

    def _execute_with_perception(self, intent: Intent, run_log: RunLog) -> str:
        """Use UI perception + LLM to handle unknown tasks."""
        max_attempts = 3

        for attempt in range(max_attempts):
            StatusBarService.show(f"👁️ Scanning UI... (attempt {attempt+1})")

            # Layer 3+4: Get scored candidates
            candidates = self.ui_layer.get_candidates(
                action_type=intent.action_type,
                goal=intent.goal,
            )

            if not candidates:
                run_log.log("ui", "no_candidates")
                return "No matching UI elements found."

            run_log.log("ui", "candidates_found", {"count": len(candidates)})
            for c in candidates:
                print(f"      {c}")

            # Layer 5: LLM picks from candidates
            StatusBarService.show("🧠 Deciding...")
            chosen_idx = self.decision_layer.pick_element(intent.goal, candidates)

            if chosen_idx is None:
                run_log.log("decision", "failed")
                return "Could not decide which element to use."

            chosen = candidates[chosen_idx]
            run_log.log("decision", "picked", {
                "index": chosen_idx,
                "element": str(chosen.element),
            })
            print(f"   🎯 Picked: {chosen}")

            # Layer 6: Execute click
            StatusBarService.show(f"▶ Clicking {chosen.element.name}")
            step = ActionStep("click", x=chosen.element.x, y=chosen.element.y)
            result = self.execution_layer.execute_step(step)
            run_log.log("execution", str(result))

            if result.success:
                # Layer 7: Verify
                verification = self.verification_layer.verify_focus_changed()
                run_log.log("verification", str(verification))

                if verification.passed:
                    return f"✅ Clicked {chosen.element.name}\n{run_log.summary()}"

            # Retry
            run_log.log("retry", f"attempt {attempt+1} failed")
            time.sleep(0.5)

        return f"Failed after {max_attempts} attempts.\n{run_log.summary()}"
