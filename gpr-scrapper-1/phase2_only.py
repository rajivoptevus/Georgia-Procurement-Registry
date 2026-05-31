"""
phase2_only.py  -  GPR Complete Scraper
========================================
Collects all 32,641 suppliers and scrapes each detail page.
Resumes from checkpoints automatically.

Run:  python phase2_only.py
"""

import json
import re
import time
import random
from datetime import datetime
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from seleniumbase import SB

BASE_URL       = "https://ssl.doas.state.ga.us/gpr"
SEARCH_URL     = f"{BASE_URL}/loadSupplierSearch?persisted=true"
DETAIL_URL     = f"{BASE_URL}/showSupplierDetails"
HEADLESS       = False
MAX_LIST_PAGES = 653
SAVE_EVERY     = 100
LIST_CP        = "checkpoint_list_all.json"
DETAIL_CP      = "checkpoint_details_progress.json"


# ── CAPTCHA ───────────────────────────────────────────────────────────────────

def solve_captcha(sb) -> bool:
    print("\n  Solving CAPTCHA ...")
    time.sleep(3)
    for attempt in range(1, 4):
        print(f"  Attempt {attempt}/3 ...")
        try:
            sb.uc_gui_click_captcha()
        except Exception as e:
            print(f"  Click error: {str(e)[:60]}")
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                token = sb.execute_script(
                    "return document.getElementById('g-recaptcha-response').value;"
                )
                if token and len(token) > 10:
                    safe = token.replace("'", "\\'")
                    sb.execute_script(f"captchaResponse = '{safe}';")
                    sb.execute_script(
                        "var e=document.getElementById('g-recaptcha-error');"
                        "if(e) e.innerHTML='';"
                    )
                    print("  CAPTCHA solved!")
                    return True
            except Exception:
                pass
            time.sleep(1)
        if attempt < 3:
            time.sleep(5)
    print("  CAPTCHA failed")
    return False


# ── List page helpers ─────────────────────────────────────────────────────────

def wait_for_table(sb, timeout=60) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            soup = BeautifulSoup(sb.get_page_source(), "html.parser")
            tbl  = soup.find("table", {"id": "supplierSearchTable"})
            if tbl:
                tbody = tbl.find("tbody")
                if tbody:
                    trs = tbody.find_all("tr")
                    if trs:
                        first = trs[0].get_text(strip=True)
                        if first and "No data" not in first:
                            print(f"  Table loaded ({len(trs)} rows)")
                            return True
        except Exception:
            pass
        time.sleep(1)
    print("  Table did not load")
    return False


def get_ids_from_datatable(sb) -> dict:
    try:
        result = sb.execute_script(
            "try{"
            "var dt=$('#supplierSearchTable').DataTable();"
            "var rows=dt.rows().data();var out={};"
            "for(var i=0;i<rows.length;i++){"
            "if(rows[i]&&rows[i].supplierId)out[i]=String(rows[i].supplierId);}"
            "return out;}catch(e){return {};}"
        )
        return result or {}
    except Exception:
        return {}


def parse_list_page(sb, page_num: int) -> list:
    id_map = get_ids_from_datatable(sb)
    soup   = BeautifulSoup(sb.get_page_source(), "html.parser")
    tbl    = soup.find("table", {"id": "supplierSearchTable"})
    if not tbl:
        return []
    tbody = tbl.find("tbody")
    if not tbody:
        return []
    rows = []
    for idx, tr in enumerate(tbody.find_all("tr")):
        tds = tr.find_all("td")
        if not tds:
            continue
        sid = (tr.get("data-supplier-id", "").strip()
               or id_map.get(str(idx), ""))
        if not sid:
            for a in tr.find_all("a", href=True):
                m = re.search(r"supplierId=([A-Za-z0-9]+)", a["href"])
                if m:
                    sid = m.group(1)
                    break
        company = tds[0].get_text(strip=True)
        if not company:
            continue
        rows.append({
            "supplier_id":    sid,
            "company":        company,
            "city":           tds[1].get_text(strip=True) if len(tds) > 1 else "",
            "state":          tds[2].get_text(strip=True) if len(tds) > 2 else "",
            "ga_resident":    tds[3].get_text(strip=True) if len(tds) > 3 else "",
            "small_business": tds[4].get_text(strip=True) if len(tds) > 4 else "",
            "list_page":      page_num,
        })
    return rows


def click_next_page(sb, current_first: str) -> bool:
    try:
        btn = sb.find_element("#supplierSearchTable_next")
        if "disabled" in (btn.get_attribute("class") or ""):
            return False
        sb.js_click("#supplierSearchTable_next")
        deadline = time.time() + 12
        while time.time() < deadline:
            time.sleep(0.5)
            soup = BeautifulSoup(sb.get_page_source(), "html.parser")
            tbl  = soup.find("table", {"id": "supplierSearchTable"})
            if tbl:
                tbody = tbl.find("tbody")
                if tbody:
                    trs = tbody.find_all("tr")
                    if trs:
                        new_first = trs[0].get_text(strip=True)
                        if new_first and new_first != current_first:
                            return True
        return True
    except Exception:
        return False


# ── Detail page parser ────────────────────────────────────────────────────────

def parse_detail_page(html: str, supplier_id: str) -> dict:
    """
    Parse GPR supplier detail page.

    Confirmed HTML structure (from detail_BID0063195.html):
    - Company info: <div class="table ... vendor_profile">
        <div class="td" data-header="Owners Ethnicity Status:">NOM</div>
    - Address: <p> tag after <h5>Address</h5>
    - Contacts: <div class="table ... contact_profile">
        thead: <div class="th">Contact Name</div> | Phone No. | Fax No.
        tbody: <div class="tr"> rows with <div class="td"> cells
    - NIGP: real <table> with NIGP Code | Description columns
    """
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "supplier_id":           supplier_id,
        "owner_ethnicity":       "",
        "company_status":        "",
        "company_class":         "",
        "ga_resident_detail":    "",
        "small_business_detail": "",
        "address":               "",
        "contact_name_1": "", "phone_1": "", "fax_1": "",
        "contact_name_2": "", "phone_2": "", "fax_2": "",
        "contact_name_3": "", "phone_3": "", "fax_3": "",
        "nigp_codes":        "",
        "nigp_descriptions": "",
        "nigp_count":        0,
    }

    # Company info from data-header attributes
    for td_div in soup.find_all("div", class_="td"):
        header = td_div.get("data-header", "").lower().rstrip(":")
        value  = td_div.get_text(strip=True)
        if not value:
            continue
        if "ethnicity" in header or "owner" in header:
            data["owner_ethnicity"] = value
        elif "company status" in header:
            data["company_status"] = data["company_status"] or value
        elif "company class" in header:
            data["company_class"] = value
        elif "ga resident" in header:
            data["ga_resident_detail"] = data["ga_resident_detail"] or value
        elif "small business" in header:
            data["small_business_detail"] = data["small_business_detail"] or value

    # Address: <p> after <h5>Address</h5>
    for h5 in soup.find_all("h5"):
        if h5.get_text(strip=True).lower() == "address":
            p = h5.find_next_sibling("p")
            if p:
                data["address"] = p.get_text(separator=" ", strip=True)
            break

    # Contacts: div-table with class contact_profile
    contact_div = soup.find("div", class_=lambda c: c and "contact_profile" in c)
    if contact_div:
        thead = contact_div.find("div", class_="thead")
        col_order = []
        if thead:
            for th in thead.find_all("div", class_="th"):
                col_order.append(th.get_text(strip=True).lower())

        tbody = contact_div.find("div", class_="tbody")
        if tbody:
            contact_idx = 1
            for tr in tbody.find_all("div", class_="tr"):
                tds = tr.find_all("div", class_="td")
                if not tds:
                    continue
                name = phone = fax = ""
                for i, td in enumerate(tds):
                    val = td.get_text(strip=True)
                    col = col_order[i] if i < len(col_order) else ""
                    if "contact" in col or "name" in col:
                        name = val
                    elif "phone" in col:
                        phone = val
                    elif "fax" in col:
                        fax = val
                    else:
                        if i == 0:
                            name = val
                        elif i == 1:
                            phone = val
                        elif i == 2:
                            fax = val
                # rh div = mobile accordion header = contact name
                if not name:
                    rh = tr.find_previous_sibling("div", class_="rh")
                    if rh:
                        name = rh.get_text(strip=True)
                if (name or phone or fax) and contact_idx <= 3:
                    data[f"contact_name_{contact_idx}"] = name
                    data[f"phone_{contact_idx}"]        = phone
                    data[f"fax_{contact_idx}"]          = fax
                    contact_idx += 1

    # NIGP codes: real <table>
    nigp_codes = []
    nigp_descs = []
    for tbl in soup.find_all("table"):
        header_row = tbl.find("tr")
        if not header_row:
            continue
        headers = [th.get_text(strip=True).lower()
                   for th in header_row.find_all(["th", "td"])]
        if not any("nigp" in h or "code" in h for h in headers):
            continue
        for tr in tbl.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) >= 2:
                code = tds[0].get_text(strip=True)
                desc = tds[1].get_text(strip=True)
                if code and code not in nigp_codes:
                    nigp_codes.append(code)
                    nigp_descs.append(desc)
            elif len(tds) == 1:
                code = tds[0].get_text(strip=True)
                if code and code not in nigp_codes:
                    nigp_codes.append(code)

    data["nigp_codes"]        = "; ".join(nigp_codes)
    data["nigp_descriptions"] = "; ".join(nigp_descs)
    data["nigp_count"]        = len(nigp_codes)
    return data


# ── Save ──────────────────────────────────────────────────────────────────────

def save_final(results: list) -> None:
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    df  = pd.DataFrame(results)
    priority = [
        "supplier_id", "company", "city", "state", "ga_resident", "small_business",
        "owner_ethnicity", "company_status", "company_class",
        "ga_resident_detail", "small_business_detail", "address",
        "contact_name_1", "phone_1", "fax_1",
        "contact_name_2", "phone_2", "fax_2",
        "contact_name_3", "phone_3", "fax_3",
        "nigp_codes", "nigp_descriptions", "nigp_count",
    ]
    cols = [c for c in priority if c in df.columns]
    cols += [c for c in df.columns if c not in priority]
    df = df[cols]
    csv_path  = f"gpr_suppliers_complete_{ts}.csv"
    json_path = f"gpr_suppliers_complete_{ts}.json"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    Path(json_path).write_text(
        json.dumps({"metadata": {"scraped_at": datetime.now().isoformat(),
                                 "total": len(results)},
                    "data": results},
                   indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n  CSV  -> {csv_path}")
    print(f"  JSON -> {json_path}")
    print(f"  Total: {len(results)} records")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("GPR COMPLETE SUPPLIER SCRAPER")
    print("=" * 60)

    # Load list checkpoint if available
    all_suppliers = []
    if Path(LIST_CP).exists():
        all_suppliers = json.loads(Path(LIST_CP).read_text(encoding="utf-8"))
        valid = sum(1 for s in all_suppliers if s.get("supplier_id"))
        print(f"\nLoaded {len(all_suppliers)} suppliers from {LIST_CP} ({valid} with IDs)")

    # Load detail checkpoint if available
    done_ids = set()
    results  = []
    if Path(DETAIL_CP).exists():
        results  = json.loads(Path(DETAIL_CP).read_text(encoding="utf-8"))
        done_ids = {r["supplier_id"] for r in results if r.get("supplier_id")}
        print(f"Loaded {len(results)} detail records from checkpoint")

    with SB(uc=True, headless=HEADLESS) as sb:

        # Phase 1: collect list if needed
        if not all_suppliers:
            print(f"\nOpening: {SEARCH_URL}")
            sb.uc_open_with_reconnect(SEARCH_URL, reconnect_time=6)
            time.sleep(3)

            if not solve_captcha(sb):
                print("CAPTCHA failed. Exiting.")
                return

            print("\nSelecting All Suppliers and searching ...")
            sb.execute_script(
                "var s=document.getElementById('supplierType');"
                "if(s){for(var i=0;i<s.options.length;i++)"
                "{s.options[i].selected=(s.options[i].value==='ALL');}}"
            )
            time.sleep(1)
            sb.js_click("#supplierSearchBtn")
            time.sleep(4)

            if not wait_for_table(sb):
                print("Table did not load. Exiting.")
                return

            print("\n" + "=" * 60)
            print("PHASE 1 - Collecting supplier list")
            print("=" * 60)

            page = 1
            while page <= MAX_LIST_PAGES:
                print(f"\nPage {page} ...", end=" ", flush=True)
                rows = parse_list_page(sb, page)
                if not rows:
                    print("no rows - stopping.")
                    break
                first_company = rows[0]["company"]
                all_suppliers.extend(rows)
                print(f"{len(rows)} rows (total: {len(all_suppliers)})")
                Path(LIST_CP).write_text(
                    json.dumps(all_suppliers, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                if not click_next_page(sb, first_company):
                    print("  Last page reached.")
                    break
                page += 1
                time.sleep(random.uniform(0.5, 1.2))

            print(f"\nPhase 1 complete: {len(all_suppliers)} suppliers")

        # Phase 2: scrape detail pages
        remaining = [s for s in all_suppliers
                     if s.get("supplier_id") and s["supplier_id"] not in done_ids]
        no_id     = [s for s in all_suppliers if not s.get("supplier_id")]

        print("\n" + "=" * 60)
        print("PHASE 2 - Scraping detail pages")
        print("=" * 60)
        print(f"  Total     : {len(all_suppliers)}")
        print(f"  Done      : {len(done_ids)}")
        print(f"  No ID     : {len(no_id)}")
        print(f"  Remaining : {len(remaining)}")

        for s in no_id:
            if s.get("company") not in {r.get("company") for r in results}:
                results.append({**s, "note": "no_supplier_id"})

        for idx, supplier in enumerate(remaining, 1):
            sid     = supplier["supplier_id"]
            company = supplier.get("company", "")[:50]
            url     = f"{DETAIL_URL}?supplierId={sid}"
            print(f"\n[{idx}/{len(remaining)}] {sid} - {company}")

            try:
                sb.uc_open_with_reconnect(url, reconnect_time=3)
                sb.wait_for_ready_state_complete()
                time.sleep(random.uniform(1.0, 2.0))

                html   = sb.get_page_source()
                detail = parse_detail_page(html, sid)
                merged = {**supplier, **detail}
                results.append(merged)
                done_ids.add(sid)

                if detail.get("contact_name_1"):
                    print(f"  Contact: {detail['contact_name_1']}  "
                          f"Phone: {detail.get('phone_1','')}  "
                          f"Fax: {detail.get('fax_1','')}")
                if detail.get("nigp_count", 0):
                    print(f"  NIGP: {detail['nigp_count']} codes")

            except Exception as exc:
                print(f"  Error: {str(exc)[:80]}")
                results.append({**supplier, "error": str(exc)})
                done_ids.add(sid)

            if idx % SAVE_EVERY == 0:
                Path(DETAIL_CP).write_text(
                    json.dumps(results, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"\n  Checkpoint: {idx}/{len(remaining)} ({idx/len(remaining)*100:.1f}%)")

        Path(DETAIL_CP).write_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        save_final(results)

        contacts = sum(1 for r in results if r.get("contact_name_1"))
        phones   = sum(1 for r in results if r.get("phone_1"))
        print("\n" + "=" * 60)
        print(f"  Total records   : {len(results)}")
        print(f"  With contacts   : {contacts}")
        print(f"  With phones     : {phones}")
        print("=" * 60)


if __name__ == "__main__":
    main()
