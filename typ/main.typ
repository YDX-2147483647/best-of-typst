#import "markdown.typ" as md
#import "projects-collection.typ": categorize-projects
#import "utils.typ": diff-month, parse-datetime, simplify-number
#import "default-config.typ": default-configuration
#import "generator.typ": generate-project

// Read data sources

#let projects = json("/build/latest.json")
#let (configuration: raw_configuration, categories: raw_categories, labels) = yaml("/projects.yaml")
#let configuration = default-configuration + raw_configuration
#let today = datetime.today()

// Calculate data

#let categories = raw_categories.map(((category, ..rest)) => (category, rest)).to-dict()
#let categorized = categorize-projects(projects, categories)
#let statistics = (
  project_count: projects.len(),
  category_count: categories.len(),
  stars_count: projects.map(p => p.star_count).sum(),
)

// Write document

#set text(lang: "en")
#set document(
  title: "Best of Typst (TCDM)",
  description: [
    A ranked list of awesome projects related to Typst,
    or the charted dark matter in Typst Universe (TCDM).
  ],
  author: "YDX-2147483647",
  keywords: ("typst", "community", "best-of", "tooling"),
)
#html.style(read("style.css"))

#show: html.main


#md.render(
  md.preprocess(read("/" + configuration.markdown_header_file), ..statistics),
  ..md.config,
)

#show outline.entry.where(level: 1): it => {
  let meta = query(selector(<category-meta>).after(it.element.location())).map(meta => meta.value).first(default: none)

  link(
    it.element.location(),
    if meta != none and meta.subtitle != none {
      html.span(title: meta.subtitle, it.body())
    } else {
      it.body()
    },
  )

  if meta != none {
    [ --- _#meta.n-projects projects_]
  }
}
#outline() <Contents>

#for (id, cat) in categorized {
  assert.eq(configuration.category_heading, "robust")

  show: html.section.with(class: "category")

  [#[= #cat.title]#label(id)]
  if "subtitle" in cat {
    md.render(cat.subtitle, ..md.config)
  }

  [#metadata((
    n-projects: cat.projects.len() + cat.hidden-projects.len(),
    subtitle: if "subtitle" in cat { cat.subtitle },
  ))<category-meta>]

  for p in cat.projects {
    list.item(generate-project(p, configuration, labels))
  }

  html.details({
    html.summary[Show #cat.hidden-projects.len() hidden projects…]
    for p in cat.hidden-projects {
      list.item(generate-project(p, configuration, labels))
    }
  })
}

#md.render(
  md.preprocess(read("/" + configuration.markdown_footer_file), ..statistics),
  ..md.config,
)
