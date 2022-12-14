#!/usr/bin/env Rscript

requireNamespace("shiny")
requireNamespace("DT")

example_query <- paste(
  "# Select variants with a MODERATE/HIGH impact and less than 10% frequency in non-Finnish Europeans:",
  "(Func_impact = 'HIGH' OR Func_impact = 'MODERATE') AND gnomAD_NFE_AF < 0.1",
  sep = "\n"
)

ui <- pageWithSidebar(
  uiOutput("title"),
  sidebarPanel(
    # Authentication
    passwordInput("password", "Please enter password:"),
    uiOutput("db_errors"),
    hr(),
    conditionalPanel(
      condition = "output.show_ui && !output.database_errors",
      # View by Genes / Contig
      radioButtons("build", "Build:", c("Hg38" = "hg38", "Hg19 (liftover)" = "hg19"), inline = TRUE),
      radioButtons("select_by", "Select variants by:", c("Gene" = "genes", "Contig" = "contig"), inline = TRUE),
      conditionalPanel(
        condition = "input.select_by === 'genes'",
        selectizeInput("genes", NULL, choices = NULL, multiple = TRUE, options = list(maxOptions = 10, maxItems = 10))
      ),
      conditionalPanel(
        condition = "input.select_by === 'contig'",
        selectInput("chr", NULL, choices = NULL),
        conditionalPanel(
          condition = "input.chr !== '[Whole genome]'",
          numericInput("min_pos", "Start position (bp):", 1, min = 1, step = 1),
          numericInput("max_pos", "End position (bp; max 10k rows shown):", NULL, min = 1, step = 1)
        )
      ),
      hr(),
      # Filters
      checkboxInput("require_pass", "Variants must PASS quality filtering", value = TRUE),
      selectInput("consequence",
        HTML("This consequence or worse (<a target='_blank' href='https://www.ensembl.org/info/genome/variation/prediction/predicted_data.html'>definitions</a>)"),
        choices = c("Any consequence")
      ),
      numericInput("min_maf", "Minimum MAF (gnomAD):", 0, min = 0, max = 1, step = 0.00001),
      numericInput("max_maf", "Maximum MAF (gnomAD):", 1, min = 0, max = 1, step = 0.00001),
      textAreaInput("query", "Filters", value = "", placeholder = example_query, rows = 3),
      uiOutput("query_errors"),
      hr(),
      # Visible columns
      selectizeInput("columns", "Visible columns", choices = c(), multiple = TRUE),
      hr(),
      # Export buttons
      downloadButton("btn_download", "Download"),
      actionButton("btn_reset", "Reset filters", icon = icon("redo-alt")),
      actionButton("btn_view_all", "All columns", icon = icon("eye")),
      actionButton("btn_view_std", "Reset columns", icon = icon("eye-slash"))
    ),
    width = 3
  ),
  mainPanel(
    tags$head(
      # https://highlightjs.org/download/
      tags$link(rel = "stylesheet", href = "highlight.v11.3.1.css"),
      tags$script(src = "highlight.v11.3.1.js"),
      # https://github.com/nodeca/pako/
      tags$head(tags$script(src = "pako_inflate.v2.0.4.js"))
    ),
    conditionalPanel(
      condition = "output.show_ui && !output.database_errors",
      tabsetPanel(
        id = "tabs",
        tabPanel("Variants", DT::dataTableOutput("table"), value = "tab_var"),
        tabPanel("Genes", DT::dataTableOutput("gene_tbl"), value = "tab_gene"),
        tabPanel("Columns", DT::dataTableOutput("columns"), value = "tab_col"),
        tabPanel("Metadata", DT::dataTableOutput("metadata"), value = "tab_meta"),
        tabPanel("JSON", uiOutput("json"), value = "tab_json")
      )
    ),
    width = 9
  )
)
