# snaptrace_web.py

  from flask import Flask, request, redirect
  from snaptrace_core import SnapTrace

  app = Flask(__name__)
  ST = SnapTrace()


  def last_reply():
      for e in reversed(ST.entries):
          if e.text.startswith("ASSISTANT:"):
              return e.text
      return ""


  @app.route("/")
  def home():
      last = last_reply()
      return f"""
      <h1>SnapTrace</h1>

      <form method="post" action="/chat">
          <textarea name="text" rows="4" style="width:100%"></textarea><br>
          <button type="submit">Send</button>
      </form>

      <h3>Last Reply</h3>
      <pre>{last}</pre>

      <a href="/dev">Developer</a>
      """


  @app.route("/chat", methods=["POST"])
  def chat():
      text = request.form.get("text", "").strip()
      if not text:
          return redirect("/")

      ok, msg = ST.add("USER:\n" + text)
      if not ok:
          return msg

      reply = f"Echo: {text}"

      ST.add("ASSISTANT:\n" + reply)
      return redirect("/")


  @app.route("/dev")
  def dev():
      status = ST.status()
      entries = "".join(
          f"<li><b>{e.index}</b>: {e.text[:80]}</li>"
          for e in ST.entries
      )

      return f"""
      <h1>Developer</h1>

      <p>Base: {status['base']} | Tail: {status['tail']}</p>

      <form method="post" action="/activate">
          <input name="idx" placeholder="Set base index"/>
          <button type="submit">Activate</button>
      </form>

      <form method="post" action="/clear">
          <button type="submit">Clear Head</button>
      </form>

      <ul>{entries}</ul>

      <a href="/">Back</a>
      """


  @app.route("/activate", methods=["POST"])
  def activate():
      idx = int(request.form.get("idx", "-1"))
      ST.activate(idx)
      return redirect("/dev")


  @app.route("/clear", methods=["POST"])
  def clear():
      ST.clear()
      return redirect("/dev")


  if __name__ == "__main__":
      app.run(host="0.0.0.0", port=8000)
  