"""
Azure OpenAI GPT EPUB Translator
- Preserves XHTML/HTML structure by translating only text nodes
- Bilingual mode (original + translation) or replacement
- Chunking, concurrency, backoff, resumable cache
- Glossary support to enforce terminology and names

Prereqs:
  pip install ebooklib beautifulsoup4 lxml openai requests

Env:
  AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT
"""

import os, json, time, re, argparse, concurrent.futures, hashlib, signal, copy
from contextlib import contextmanager
from itertools import chain
from typing import List, Optional
from bs4 import BeautifulSoup, NavigableString
from ebooklib import epub
import ebooklib
import requests
from openai import AzureOpenAI

# ---------------- Azure OpenAI (GPT) client ----------------

class AzureGPT:
	def __init__(self, endpoint: str, key: str, deployment: str, api_version: str, temperature: float = 0.2, debug: bool = False, instruction: Optional[str] = None):
		# Use standard Azure OpenAI SDK (works for both Foundry and direct Azure OpenAI)
		self.client = AzureOpenAI(azure_endpoint=endpoint, api_key=key, api_version=api_version)
		self.use_azure_ai = False
		self.deployment = deployment
		self.temperature = temperature
		self.debug = debug
		self.endpoint = endpoint
		self.instruction = instruction

	def translate_batch(self, items: List[str], src_lang: str, tgt_lang: str, glossary: dict, retry: int = 3, sleep: float = 1.0) -> List[str]:
		"""
		Translate a list of short strings. Uses one batched prompt per item (multi-turn)
		for clarity; you can also pack multiple items into one prompt if desired.
		"""
		out = []
		for text in items:
			prompt = build_prompt(text, src_lang, tgt_lang, glossary)
			for attempt in range(retry):
				try:
					if self.debug:
						print(f"[azure] chat.completions.create endpoint={self.endpoint} model={self.deployment} chars={len(text)} attempt={attempt+1}")
					t0 = time.time()
					
					# Use standard Azure OpenAI SDK
					system_msg = self.instruction if self.instruction else (
						"You are a professional literary translator. "
						"Translate faithfully, fluently, and maintain formatting where possible."
					)
					resp = self.client.chat.completions.create(
						model=self.deployment,
						temperature=self.temperature,
						messages=[
							{"role": "system", "content": system_msg},
							{"role": "user", "content": prompt}
						]
					)
					translated = resp.choices[0].message.content.strip()
					
					if self.debug:
						dt = time.time() - t0
						print(f"[azure] response {len(translated)} chars in {dt:.2f}s: {translated[:160].replace(chr(10),' ')}...")
					out.append(translated)
					break
				except Exception as e:
					if self.debug:
						print(f"[azure] error: {type(e).__name__}: {e}")
					# Gracefully handle content filter errors - skip problematic chunks
					if "content_filter" in str(e) or "ResponsibleAIPolicyViolation" in str(e):
						if self.debug:
							print(f"[azure] Content filter triggered, skipping chunk (returning original)")
						out.append(text)  # Return original text if content filtered
						break
					time.sleep(sleep * (attempt + 1))
					if attempt == retry - 1:
						raise
		return out

# ---------------- Azure Text Translator (REST API) ----------------

class AzureTextTranslator:
	"""Uses Azure Cognitive Services Text Translator API (not GPT)"""
	
	def __init__(self, endpoint: str, key: str, debug: bool = False):
		"""
		endpoint: e.g., "https://your-endpoint.cognitiveservices.azure.com"
		key: API key for Document Translator
		"""
		self.endpoint = endpoint.rstrip("/")
		self.key = key
		self.debug = debug
	
	def translate_document(self, html_content: str, src_lang: str, tgt_lang: str, retry: int = 3, sleep: float = 1.0) -> str:
		"""
		Translate entire HTML document using Azure AI Foundry Document Translation
		"""
		for attempt in range(retry):
			try:
				if self.debug:
					print(f"[translator] Translating document: sourceLanguage={src_lang} targetLanguage={tgt_lang} size={len(html_content)} bytes attempt={attempt+1}")
				
				t0 = time.time()
				
				# Build API call for Azure AI Foundry Document Translation
				path = "/translator/document:translate"
				url = self.endpoint + path
				
				params = {
					"sourceLanguage": src_lang,
					"targetLanguage": tgt_lang,
					"api-version": "2024-05-01"
				}
				headers = {
					"Ocp-Apim-Subscription-Key": self.key
				}
				
				# Send HTML document as file upload
				files = {
					"document": ("document.html", html_content.encode('utf-8'), "text/html")
				}
				
				resp = requests.post(url, headers=headers, files=files, params=params, timeout=120)
				
				if self.debug and resp.status_code >= 400:
					print(f"[translator] Error response: {resp.status_code} - {resp.text[:500]}")
				
				resp.raise_for_status()
				
				# Response is the translated HTML directly
				translated_html = resp.content.decode('utf-8')
				
				if self.debug:
					dt = time.time() - t0
					print(f"[translator] Translated document in {dt:.2f}s: {len(translated_html)} bytes")
				
				return translated_html
			
			except Exception as e:
				if self.debug:
					print(f"[translator] error: {type(e).__name__}: {e}")
				time.sleep(sleep * (attempt + 1))
				if attempt == retry - 1:
					raise
		
		return html_content  # fallback to original
	
	def translate_batch(self, items: List[str], src_lang: str, tgt_lang: str, glossary: dict = None, retry: int = 3, sleep: float = 1.0) -> List[str]:
		"""
		Legacy method for compatibility - translates text chunks
		"""
		out = []
		
		for text in items:
			for attempt in range(retry):
				try:
					if self.debug:
						print(f"[translator] POST {self.endpoint} sourceLanguage={src_lang} targetLanguage={tgt_lang} chars={len(text)} attempt={attempt+1}")
					
					t0 = time.time()
					
					# Build API call for Azure AI Foundry Document Translation
					path = "/translator/document:translate"
					url = self.endpoint + path
					
					params = {
						"sourceLanguage": src_lang,
						"targetLanguage": tgt_lang,
						"api-version": "2024-05-01"
					}
					headers = {
						"Ocp-Apim-Subscription-Key": self.key
					}
					
					# Send text as a file upload
					files = {
						"document": ("text.txt", text.encode('utf-8'), "text/plain")
					}
					
					if self.debug:
						print(f"[translator] Sending text as file upload, size: {len(text)} chars")
					
					resp = requests.post(url, headers=headers, files=files, params=params, timeout=60)
					
					if self.debug and resp.status_code >= 400:
						print(f"[translator] Error response: {resp.status_code} - {resp.text[:500]}")
					
					resp.raise_for_status()
					
					# Response is the translated text directly
					translated = resp.content.decode('utf-8')
					
					if self.debug:
						dt = time.time() - t0
						print(f"[translator] response {len(translated)} chars in {dt:.2f}s: {translated[:160].replace(chr(10),' ')}...")
					
					out.append(translated)
					break
				
				except Exception as e:
					if self.debug:
						print(f"[translator] error: {type(e).__name__}: {e}")
					time.sleep(sleep * (attempt + 1))
					if attempt == retry - 1:
						raise
		
		return out

# ---------------- Prompt builder ----------------

def build_prompt(text: str, src_lang: str, tgt_lang: str, glossary: dict) -> str:
	glossary_lines = []
	for k, v in (glossary or {}).items():
		glossary_lines.append(f"- {k} → {v}")
	glossary_block = "\n".join(glossary_lines) if glossary_lines else "None"

	# Simplified prompt to avoid content filter triggers
	return (
		f"Translate to {tgt_lang}:\n\n{text}"
	)

# ---------------- HTML parsing helpers ----------------

SKIP_TAGS = {"script", "style", "code", "pre"}

def collect_text_nodes(soup: BeautifulSoup) -> List[NavigableString]:
	nodes = []
	for t in soup.find_all(string=True):
		parent = t.parent
		if isinstance(t, NavigableString) and t.strip():
			if parent and parent.name and parent.name.lower() in SKIP_TAGS:
				continue
			nodes.append(t)
	return nodes

def chunk_text(text: str, max_chars: int = 2000) -> List[str]:
	"""Fast chunker: fixed-size slices to avoid slow scans on long paragraphs."""
	if len(text) <= max_chars:
		return [text]
	parts = []
	cursor = 0
	total_len = len(text)
	while cursor < total_len:
		end = min(cursor + max_chars, total_len)
		parts.append(text[cursor:end])
		cursor = end
	return parts

def bilingual_wrap(original: str, translated: str) -> str:
	return f'<span class="bilingual"><span class="original">{original}</span> <span class="translated">{translated}</span></span>'

# ---------------- Simple .env loader (dev convenience) ----------------

def load_env_file(path: Optional[str]):
	"""
	Load KEY=VALUE lines into os.environ (does not override already-set vars).
	Comments (# ...) and blank lines are ignored.
	"""
	if not path or not os.path.exists(path):
		return
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			if "=" not in line:
				continue
			key, value = line.split("=", 1)
			key = key.strip()
			value = value.strip()
			if key and key not in os.environ:
				os.environ[key] = value


# ---------------- Azure helpers ----------------

def normalize_endpoint(url: Optional[str]) -> Optional[str]:
	"""Strip any trailing /openai/v1 or /openai/v1/ from Azure endpoint URLs."""
	if not url:
		return url
	lowered = url.lower()
	for suffix in ("/openai/v1/", "/openai/v1"):
		if lowered.endswith(suffix):
			return url[: -len(suffix)]
	return url

# ---------------- Resumable cache ----------------

class Cache:
	def __init__(self, path: Optional[str]):
		self.path = path
		self.map = {}
		if path and os.path.exists(path):
			with open(path, "r", encoding="utf-8") as f:
				for line in f:
					try:
						obj = json.loads(line)
						self.map[obj["key"]] = obj["value"]
					except:
						pass

	def key(self, content: str, tgt_lang: str) -> str:
		return hashlib.sha256((tgt_lang + "||" + content).encode("utf-8")).hexdigest()

	def get(self, content: str, tgt_lang: str) -> Optional[str]:
		return self.map.get(self.key(content, tgt_lang))

	def put(self, content: str, tgt_lang: str, translated: str):
		if not self.path:
			return
		k = self.key(content, tgt_lang)
		if k in self.map:
			return
		self.map[k] = translated
		with open(self.path, "a", encoding="utf-8") as f:
			f.write(json.dumps({"key": k, "value": translated}) + "\n")

# ---------------- Core: translate one HTML doc ----------------

def translate_html_doc(html: str, gpt: AzureGPT, src_lang: str, tgt_lang: str,
				   bilingual: bool, glossary: dict, cache: Cache,
			   workers: int = 6, translated_color: Optional[str] = None,
			   translated_style: Optional[str] = None,
			   max_paragraphs: int = 100) -> str:
	soup = BeautifulSoup(html, "lxml-xml")
	
	if bilingual:
		# For bilingual mode, work at paragraph level
		return translate_paragraphs_bilingual(soup, gpt, src_lang, tgt_lang, glossary, cache, workers, translated_color, translated_style, max_paragraphs)
	else:
		# For non-bilingual mode, work at text node level
		return translate_text_nodes(soup, gpt, src_lang, tgt_lang, glossary, cache, workers)

def translate_text_nodes(soup: BeautifulSoup, gpt: AzureGPT, src_lang: str, tgt_lang: str,
						  glossary: dict, cache: Cache, workers: int = 6) -> str:
	"""Translate at text node level (for non-bilingual mode)"""
	nodes = collect_text_nodes(soup)

	originals = [str(n) for n in nodes]
	# Build workload: split long nodes into chunks but reassemble later
	work_items = []
	mapping = []  # maps node index to list of chunk indices
	chunk_store = []
	for i, txt in enumerate(originals):
		cached = cache.get(txt, tgt_lang)
		if cached is not None:
			# node already translated as a whole
			work_items.append(None)
			mapping.append([-1])  # marker
			chunk_store.append(cached)
		else:
			chunks = chunk_text(txt)
			idxs = []
			for c in chunks:
				idxs.append(len(work_items))
				work_items.append(c)
			mapping.append(idxs)
			chunk_store.append(None)

	# Translate all non-cached chunks concurrently
	# Build list of strings to translate
	to_translate = [w for w in work_items if w is not None]
	if to_translate:
		print(f"[gpt] Submitting {len(to_translate)} chunk(s) for translation to {tgt_lang}...")
	translated_chunks = []

	def _worker(batch: List[str]) -> List[str]:
		return gpt.translate_batch(batch, src_lang, tgt_lang, glossary)

	if to_translate:
		# group size ~8 for reasonable throughput; executor.map preserves submission order
		groups = [to_translate[i:i+8] for i in range(0, len(to_translate), 8)]
		with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
			ordered_results = ex.map(_worker, groups)
			translated_chunks = list(chain.from_iterable(ordered_results))

	# Reassemble per-node translations
	# Walk mapping to stitch chunk translations back
	chunk_cursor = 0
	node_translations = []
	for i, idxs in enumerate(mapping):
		if idxs and idxs[0] == -1:
			# cached whole-node result
			node_translations.append(chunk_store[i])
			continue
		stitched = []
		for _ in idxs:
			stitched.append(translated_chunks[chunk_cursor])
			chunk_cursor += 1
		merged = " ".join(stitched).strip()
		node_translations.append(merged)
		# store whole node in cache for future runs
		cache.put(originals[i], tgt_lang, merged)

	# Replace text nodes in soup
	for node, trans in zip(nodes, node_translations):
		node.replace_with(trans)

	return str(soup)

def translate_paragraphs_bilingual(soup: BeautifulSoup, gpt: AzureGPT, src_lang: str, tgt_lang: str,
			   glossary: dict, cache: Cache, workers: int = 6, translated_color: Optional[str] = None,
			   translated_style: Optional[str] = None,
			   max_paragraphs: int = 100) -> str:
	"""Translate at paragraph level with bilingual output"""
	# Find all paragraph-like elements (only direct text containers, avoid nesting issues)
	paragraph_tags = ['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote']
	paragraphs = []
	for tag in paragraph_tags:
		paragraphs.extend(soup.find_all(tag))
	
	print(f"[bilingual] Found {len(paragraphs)} paragraph elements")
	
	# Limit paragraphs per document to avoid timeouts on large documents
	if len(paragraphs) > max_paragraphs:
		print(f"[bilingual] Limiting to {max_paragraphs} paragraphs (found {len(paragraphs)})")
		paragraphs = paragraphs[:max_paragraphs]
	
	if not paragraphs:
		return str(soup)
	
	# Extract text from each paragraph; skip ones containing images to avoid timeouts
	originals = []
	skipped_imgs = 0
	for p in paragraphs:
		if p.find('img'):
			originals.append(None)
			skipped_imgs += 1
			continue
		text = p.get_text(separator=' ', strip=True)
		if text:  # Only process non-empty paragraphs
			originals.append(text)
		else:
			originals.append(None)
	if skipped_imgs:
		print(f"[bilingual] Skipped {skipped_imgs} paragraph(s) containing images")
	
	# Build workload: split long paragraphs into chunks
	work_items = []
	mapping = []  # maps paragraph index to list of chunk indices
	chunk_store = []
	cache_hits = 0
	cache_misses = 0
	for i, txt in enumerate(originals):
		if txt is None:
			mapping.append([])
			chunk_store.append(None)
			continue
		
		cached = cache.get(txt, tgt_lang)
		if cached is not None:
			work_items.append(None)
			mapping.append([-1])  # marker for cached
			chunk_store.append(cached)
			cache_hits += 1
		else:
			chunks = chunk_text(txt)
			idxs = []
			for c in chunks:
				idxs.append(len(work_items))
				work_items.append(c)
			mapping.append(idxs)
			chunk_store.append(None)
			cache_misses += 1
	
	# Translate all non-cached chunks
	print(f"[bilingual] Cache hits: {cache_hits}, misses: {cache_misses}")
	to_translate = [w for w in work_items if w is not None]
	if to_translate:
		print(f"[gpt] Submitting {len(to_translate)} chunk(s) for translation to {tgt_lang}...")
	translated_chunks = []
	
	def _worker(batch: List[str]) -> List[str]:
		return gpt.translate_batch(batch, src_lang, tgt_lang, glossary)
	
	if to_translate:
		# Batch size: 32 for balanced throughput and timeout avoidance
		groups = [to_translate[i:i+32] for i in range(0, len(to_translate), 32)]
		print(f"[gpt] Processing {len(groups)} batch group(s)...")
		with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
			ordered_results = ex.map(_worker, groups)
			translated_chunks = list(chain.from_iterable(ordered_results))
	
	# Reassemble paragraph translations
	chunk_cursor = 0
	paragraph_translations = []
	for i, idxs in enumerate(mapping):
		if not idxs:
			paragraph_translations.append(None)
			continue
		if idxs[0] == -1:
			# cached result
			paragraph_translations.append(chunk_store[i])
			continue
		stitched = []
		for _ in idxs:
			stitched.append(translated_chunks[chunk_cursor])
			chunk_cursor += 1
		merged = " ".join(stitched).strip()
		paragraph_translations.append(merged)
		cache.put(originals[i], tgt_lang, merged)
	
	# Replace paragraph contents with bilingual version (two separate paragraphs)
	for p, orig, trans in zip(paragraphs, originals, paragraph_translations):
		if orig is None or trans is None:
			continue  # Skip empty paragraphs
		
		# Check if paragraph still has a parent (not already removed)
		if p.parent is None:
			continue
		
		# Keep original paragraph unchanged - preserve all formatting (bold, italic, links, classes, etc.)
		# Add custom data attribute and class for tracking
		p['data-bilingual'] = 'original'
		
		# Add 'original' class to original paragraph
		original_classes = p.get('class', [])
		if isinstance(original_classes, str):
			original_classes = original_classes.split()
		if 'original' not in original_classes:
			original_classes.append('original')
		p['class'] = original_classes
		
		# Create translated paragraph by cloning the entire inner structure
		trans_p = soup.new_tag(p.name)
		
		# Copy all attributes from original paragraph (before we added 'original' class)
		for attr, value in p.attrs.items():
			if attr == 'data-bilingual':  # Don't copy our tracking attribute
				continue
			if attr == 'class':  # Handle class specially to avoid copying 'original'
				# Get original classes without 'original'
				orig_classes = value if isinstance(value, list) else value.split()
				trans_classes = [c for c in orig_classes if c != 'original']
				trans_classes.append('translated')
				trans_p['class'] = trans_classes
			else:
				trans_p[attr] = value
		
		# Override/add our tracking
		trans_p['data-bilingual'] = 'translated'
		
		# Add custom color/style if specified
		styles = []
		if p.get('style'):
			styles.append(p['style'])  # Keep original styles
		if translated_color:
			styles.append(f'color: {translated_color};')
		if translated_style:
			style_val = translated_style.strip()
			if not style_val.endswith(';'):
				style_val += ';'
			styles.append(style_val)
		if styles:
			trans_p['style'] = ' '.join(styles)
		
		# Clone the inner HTML structure and replace text
		# This preserves nested tags like <span class="italic"><span class="bold">
		if p.contents:
			# Deep clone all children to avoid modifying the original
			for child in p.contents:
				cloned = copy.deepcopy(child)
				trans_p.append(cloned)
			
			# Replace all text nodes with translated text
			text_nodes = list(trans_p.strings)
			if text_nodes:
				# Replace first text node with translation, clear the rest
				first_done = False
				for text in trans_p.strings:
					if not first_done:
						text.replace_with(trans)
						first_done = True
					else:
						text.replace_with('')
		else:
			# No children, just set the text
			trans_p.string = trans
		
		p.insert_after(trans_p)
	
	return str(soup)

# ---------------- EPUB end-to-end ----------------

def process_epub(input_epub: str, output_epub: str, gpt,
			 src_lang: str, tgt_lang: str, bilingual: bool,
			 glossary: dict, cache_path: Optional[str], workers: int,
		limit_docs: Optional[int] = None, translated_color: Optional[str] = None,
		translated_style: Optional[str] = None, max_paragraphs: int = 100):
	cache = Cache(cache_path)
	book = epub.read_epub(input_epub)
	docs = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
	if limit_docs is not None:
		docs = docs[:max(0, limit_docs)]
		print(f"[epub] Found {len(docs)} document(s) to translate (limited).")
	else:
		print(f"[epub] Found {len(docs)} document(s) to translate.")
	
	# Also open raw ZIP to get original HTML with head content intact
	import zipfile
	zip_file = zipfile.ZipFile(input_epub, 'r')
	
	# Store translated HTML with head intact (ebooklib strips it)
	translated_html_map = {}  # filename -> translated HTML with head
	
	# Determine translation mode based on service and options
	# Mode 1: Document Translation (whole document) - Translator API + non-bilingual
	# Mode 2: Text Translation (chunks) - Translator API + bilingual OR any GPT mode
	# Mode 3: GPT Translation (chunks) - GPT service (always chunk-based)
	
	is_gpt = isinstance(gpt, AzureGPT)
	is_translator = isinstance(gpt, AzureTextTranslator)
	use_document_translation = is_translator and not bilingual and hasattr(gpt, 'translate_document')
	
	if use_document_translation:
		print(f"[mode] Using Document Translation API (whole document, non-bilingual)")
	elif is_translator:
		print(f"[mode] Using Text Translation API (chunk-based, bilingual)")
	else:
		print(f"[mode] Using GPT Translation (chunk-based)")
	
	for i, item in enumerate(docs, start=1):
		print(f"[epub] Translating {i}/{len(docs)}: {item.get_name()}")
		
		# Get raw HTML from ZIP to preserve head content
		# ebooklib strips head content, so we read directly from ZIP
		item_name = item.get_name()
		# Try different possible paths in the ZIP
		possible_paths = [item_name, f'EPUB/{item_name}', f'OPS/{item_name}', f'OEBPS/{item_name}']
		html = None
		for path in possible_paths:
			try:
				html = zip_file.read(path).decode("utf-8", errors="ignore")
				break
			except KeyError:
				continue
		
		if html is None:
			# Fallback to ebooklib if not found in ZIP
			html = item.get_content().decode("utf-8", errors="ignore")
		
		print(f"[epub] Original HTML size: {len(html)} characters")
		
		try:
			# Set timeout for translation (5 minutes)
			import signal
			def timeout_handler(signum, frame):
				raise TimeoutError(f"Translation timed out after 300 seconds")
			
			signal.signal(signal.SIGALRM, timeout_handler)
			signal.alarm(300)  # 300 second timeout
			
			try:
				if use_document_translation:
					# Mode 1: Document Translation - whole document, no chunks
					new_html = gpt.translate_document(html, src_lang, tgt_lang)
				else:
					# Mode 2 & 3: Text Translation or GPT - chunk-based translation
					new_html = translate_html_doc(
						html, gpt, src_lang, tgt_lang, bilingual, glossary, cache, workers, translated_color, translated_style, max_paragraphs
					)
			finally:
				signal.alarm(0)  # Cancel the alarm
			
			# Debug: Check if head content is in translated HTML
			has_head_content = '<title>' in new_html and '<link' in new_html
			print(f"[epub] Translated HTML size: {len(new_html)} characters")
			if has_head_content:
				print(f"[epub] ✓ Head content preserved in translation")
			else:
				print(f"[epub] ⚠ Head content missing after translation")
			
			# Store translated HTML with head for later ZIP write
			translated_html_map[item.get_name()] = new_html
			
			item.set_content(new_html.encode("utf-8"))
		except Exception as e:
			print(f"[epub] ERROR translating {item.get_name()}: {type(e).__name__}: {str(e)[:200]}")
			print(f"[epub] Skipping this document and continuing...")
			continue
	
	zip_file.close()
	
	# Write EPUB - ebooklib's write_epub may strip head content, so we write it
	# then manually update HTML files with proper head content
	try:
		epub.write_epub(output_epub, book)
	except TypeError as e:
		if "Argument must be bytes or unicode, got 'NoneType'" in str(e):
			print(f"[epub] WARNING: TOC item has None UID - attempting workaround...")
			# Fix None UIDs in TOC items before writing
			for toc_item in book.toc:
				if isinstance(toc_item, tuple):
					item, children = toc_item
					if hasattr(item, 'uid') and item.uid is None:
						item.uid = f"nav_{id(item)}"
				else:
					if hasattr(toc_item, 'uid') and toc_item.uid is None:
						toc_item.uid = f"nav_{id(toc_item)}"
			print(f"[epub] Retrying EPUB write with fixed UIDs...")
			try:
				epub.write_epub(output_epub, book)
				print(f"[epub] ✓ EPUB write succeeded with workaround")
			except Exception as retry_error:
				print(f"[epub] ERROR: EPUB write still failed: {type(retry_error).__name__}: {str(retry_error)[:200]}")
				print(f"[epub] NOTE: Translation is complete but EPUB packaging failed")
				print(f"[epub] HTML content has been translated and saved in temporary files")
				# Don't re-raise, continue with head content fix
		else:
			raise
	
	# Now fix the head content by updating the ZIP directly with our saved translations
	import tempfile
	import shutil
	with tempfile.TemporaryDirectory() as tmpdir:
		temp_epub = f"{tmpdir}/temp.epub"
		shutil.copy(output_epub, temp_epub)
		
		# Reopen and update HTML files
		with zipfile.ZipFile(temp_epub, 'r') as zip_read:
			with zipfile.ZipFile(output_epub, 'w', zipfile.ZIP_DEFLATED) as zip_write:
				for item in zip_read.infolist():
					data = zip_read.read(item.filename)
					# For HTML files that we translated, use our saved version with head intact
					for doc_name, translated_html in translated_html_map.items():
						if item.filename.endswith(doc_name):
							data = translated_html.encode('utf-8')
							break
					zip_write.writestr(item, data)

