<template>
  <div class="markdown-body" v-html="renderedHtml" @click="handleLinkClick"></div>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'
import MarkdownIt from 'markdown-it'
// @ts-ignore
import mk from 'markdown-it-katex'

// Import styles
import 'github-markdown-css/github-markdown-dark.css'
import 'katex/dist/katex.min.css'

const props = defineProps<{
  content: string
}>()

const emit = defineEmits(['wiki-link'])

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
})

md.use(mk)

const renderedHtml = computed(() => {
  if (!props.content) return ''
  
  // Pre-process wikilinks: [[Node Name]] -> <a href="#" class="wiki-link" data-target="Node Name">Node Name</a>
  const preProcessed = props.content.replace(/\[\[(.*?)\]\]/g, (match, p1) => {
    return `<a href="#" class="wiki-link" data-target="${p1}">[[${p1}]]</a>`
  })
  
  return md.render(preProcessed)
})

function handleLinkClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (target && target.classList.contains('wiki-link')) {
    e.preventDefault()
    e.stopPropagation()
    const nodeName = target.getAttribute('data-target')
    if (nodeName) {
      emit('wiki-link', nodeName)
    }
  }
}
</script>

<style scoped>
.markdown-body {
  box-sizing: border-box;
  width: 100%;
  margin: 0;
  padding: 0;
  background: transparent !important;
  font-family: 'Space Mono', monospace;
  font-size: 14px;
  color: #F4F4F0;
}

/* Custom overrides for the dark theme to match our aesthetic */
.markdown-body :deep(h1), 
.markdown-body :deep(h2), 
.markdown-body :deep(h3), 
.markdown-body :deep(h4), 
.markdown-body :deep(h5), 
.markdown-body :deep(h6) {
  color: #E03C31;
  border-bottom: 1px solid #1A1A1A;
}

.markdown-body :deep(a) {
  color: #00FF41;
}

.markdown-body :deep(code) {
  background-color: #1A1A1A;
  color: #F2C12E;
  font-family: 'Space Mono', monospace;
}

.markdown-body :deep(pre) {
  background-color: #050505;
  border: 1px solid #1A1A1A;
}

.markdown-body :deep(blockquote) {
  color: #888;
  border-left: 4px solid #005096;
}

.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  border: 1px solid #1A1A1A;
}

.markdown-body :deep(table tr:nth-child(2n)) {
  background-color: #111;
}
</style>
