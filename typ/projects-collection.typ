/// A simplified version of `best_of.projects_collection.categorize_projects`.
///
/// Returns categories with `projects` and `hidden-projects` populated.
#let categorize-projects(projects, categories) = {
  // We can't `let … = categories.at(…)` here, or the variable `categories` won't be updated.

  for id in categories.keys() {
    categories.at(id).insert("projects", ())
    categories.at(id).insert("hidden-projects", ())
  }

  for p in projects {
    if p.show {
      categories.at(p.category).projects.push(p)
    } else {
      categories.at(p.category).hidden-projects.push(p)
    }
  }

  categories
}
