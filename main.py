import fitz  # PyMuPDF
import re

def modify_statement_final_match(
    input_pdf, 
    output_pdf, 
    old_name, 
    new_name, 
    old_account, 
    new_account, 
    keep_unedited_pages=False
):
    src_doc = fitz.open(input_pdf)
    total_src_pages = len(src_doc)
    
    # Target indices from original document
    target_indices = [0, 1, total_src_pages - 2, total_src_pages - 1]
    
    # Fixed static page labels to use when extracting only the target pages
    fixed_page_labels = ["1/82", "2/82", "81/82", "82/82"]
    
    # Initialize an empty document
    out_doc = fitz.open()
    
    # Determine which pages we are processing
    pages_to_process = list(range(total_src_pages)) if keep_unedited_pages else target_indices

    for idx_counter, old_idx in enumerate(pages_to_process):
        if old_idx < 0 or old_idx >= total_src_pages:
            continue
            
        # Copy the original page over
        out_doc.insert_pdf(src_doc, from_page=old_idx, to_page=old_idx)
        page = out_doc[-1] # Work on the newly appended page
        
        # --- 1. Precise Name Replacements ---
        name_instances = page.search_for(old_name)
        for rect in name_instances:
            is_top_left = rect.x0 < 100
            if is_top_left:
                final_font = "Helvetica"
                final_size = 8.0      
                y_nudge = 8.0         
            else:
                final_font = "Times-Roman"
                final_size = 10.0            
                y_nudge = 8.5         
            
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            
            adjusted_point = fitz.Point(rect.x0, rect.y0 + y_nudge)
            page.insert_text(adjusted_point, new_name, fontsize=final_size, fontname=final_font)
            
        # --- 2. Precise Account Number Replacements ---
        account_instances = page.search_for(old_account)
        for rect in account_instances:
            final_font = "Times-Roman"       
            final_size = 10.0                
            y_nudge = 8.5             
            
            page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            
            adjusted_point = fitz.Point(rect.x0, rect.y0 + y_nudge)
            page.insert_text(adjusted_point, new_account, fontsize=final_size, fontname=final_font)

        # --- 3. Fixed Page Number Correction ---
        text_page = page.get_text("dict")
        for block in text_page["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if re.search(r'\d+/\d+', text):
                            span_rect = fitz.Rect(span["bbox"])
                            
                            # Decide what text format to use based on the keep_unedited_pages option
                            if not keep_unedited_pages and idx_counter < len(fixed_page_labels):
                                label_fraction = fixed_page_labels[idx_counter]
                            else:
                                # Fallback fallback if keeping all pages
                                label_fraction = f"{idx_counter + 1}/{total_src_pages}"
                            
                            if "Page" in text:
                                new_page_str = f"Page :{label_fraction}"
                            else:
                                new_page_str = label_fraction
                            
                            page.add_redact_annot(span_rect, fill=(1, 1, 1))
                            page.apply_redactions()
                            
                            adjusted_point = fitz.Point(span_rect.x0, span["origin"][1])
                            page.insert_text(
                                adjusted_point, 
                                new_page_str, 
                                fontsize=span["size"], 
                                fontname="tibo"  # Core abbreviation for Times-Bold
                            )

    out_doc.save(output_pdf, garbage=4, deflate=True)
    print(f"Perfected output successfully generated: {output_pdf} ({len(pages_to_process)} pages)")

# Execute implementation match
modify_statement_final_match(
    input_pdf="EYOB STMNT.pdf", 
    output_pdf="PERFECT_MATCH_STMNT.pdf",
    old_name="EYOB LEMA TULU",
    new_name="EYOB LEMA TULU",
    old_account="1000374966368",
    new_account="1000305725467",
    keep_unedited_pages=False  # Extract and number ONLY the target pages using the static list
)