/// A simplified version of `best_of.utils.simplify_number`.
/// - num (int):
/// -> str
#let simplify-number(num) = {
  let magnitude = 0
  while calc.abs(num) >= 1000 {
    magnitude += 1
    num /= 1000.0
  }

  str(num).replace(regex("\.\d+$"), "")
  ("", "K", "M", "B", "T").at(magnitude)
}
#{
  assert.eq(simplify-number(193), "193")
  assert.eq(simplify-number(-193), "−193")
  assert.eq(simplify-number(10.0), "10")
  assert.eq(simplify-number(26366), "26K")
}

/// Parse a string as datetime.
/// https://github.com/typst/typst/issues/4107
#let parse-datetime(s) = {
  // We have to discard the milliseconds, or it will become `$__toml_private_datetime`.
  let t = toml(bytes("date = " + s.replace(regex("\.\d+$"), "")))
  t.date
}

/// Equivalent to `best_of.utils.diff_month`.
///
/// Returns (a - b) / month, with an error up to two months.
///
/// - a (datetime):
/// - b (datetime):
/// -> int
#let diff-month(a, b) = {
  return (a.year() - b.year()) * 12 + a.month() - b.month()
}
