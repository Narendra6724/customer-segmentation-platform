"""
Streamlit Dashboard — Customer Segmentation Platform v2
Pages: Login | Prediction | Analytics | CSV Upload | Admin Panel
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib
import io

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Customer Segmentation AI",
    page_icon="🎯",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 2rem; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card h2 { margin: 0; font-size: 2rem; }
    .metric-card p  { margin: 0; font-size: 0.9rem; opacity: 0.85; }
    .insight-box {
        background: #f0f2f6;
        border-left: 5px solid #667eea;
        padding: 1rem 1.2rem;
        border-radius: 6px;
        margin-top: 1rem;
    }
    .login-header {
        text-align: center;
        padding: 2rem 0 0.5rem 0;
    }
    .login-header h1 { font-size: 2.2rem; margin-bottom: 0.2rem; }
    .login-header p  { color: #888; font-size: 1rem; }
    .cluster-legend {
        background: #1e1e2f;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .cluster-legend h4 { color: #ccc; margin: 0 0 0.6rem 0; }
    .cluster-legend .item {
        display: flex; align-items: center; gap: 8px;
        margin-bottom: 4px; font-size: 0.88rem; color: #ddd;
    }
    .cluster-legend .dot {
        width: 12px; height: 12px; border-radius: 50%; display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

CLUSTER_COLORS = {
    0: "#636EFA",
    1: "#00CC96",
    2: "#EF553B",
    3: "#AB63FA",
    4: "#FFA15A",
}

CLUSTER_LABELS = {
    0: "Average Customers",
    1: "Premium Customers",
    2: "Target Customers",
    3: "Low-value Customers",
    4: "Risk Customers",
}

CLUSTER_DESCRIPTIONS = {
    0: "Moderate income & spending — mainstream segment",
    1: "High income & high spending — most valuable",
    2: "Low income but high spending — enthusiastic buyers",
    3: "Low income & low spending — minimal revenue",
    4: "High income but low spending — potential to convert",
}

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
for key, default in [
    ("logged_in", False),
    ("user_email", ""),
    ("user_role", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ═══════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════
def show_login():
    st.markdown(
        '<div class="login-header">'
        "<h1>🎯 Customer Segmentation AI</h1>"
        "<p>Enterprise Analytics Platform</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    _, center, _ = st.columns([1.2, 1.6, 1.2])
    with center:
        with st.form("login_form"):
            st.subheader("🔒 Sign In")
            email = st.text_input("Email", placeholder="yourname@mgit.ac.in")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    try:
                        resp = requests.post(
                            f"{API_URL}/auth/login",
                            json={"email": email.strip(), "password": password},
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.logged_in = True
                            st.session_state.user_email = data["email"]
                            st.session_state.user_role = data["role"]
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password.")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Cannot connect to backend. Is the API server running?")

        st.markdown(
            "<div style='text-align:center; color:#666; font-size:0.8rem; margin-top:1rem;'>"
            "Default password for all accounts: <b>12345678</b>"
            "</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════
# HELPER — cluster legend HTML
# ═══════════════════════════════════════════════════════════════════════════
def render_cluster_legend():
    items = ""
    for cid in sorted(CLUSTER_LABELS.keys()):
        items += (
            f'<div class="item">'
            f'<span class="dot" style="background:{CLUSTER_COLORS[cid]};"></span>'
            f'<span><b>{CLUSTER_LABELS[cid]}</b> — {CLUSTER_DESCRIPTIONS[cid]}</span>'
            f'</div>'
        )
    st.markdown(
        f'<div class="cluster-legend"><h4>📌 Cluster Legend</h4>{items}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════
def show_app():
    is_admin = st.session_state.user_role == "admin"

    # --- Sidebar ---
    st.sidebar.title("🎯 Segmentation AI")
    st.sidebar.markdown(f"**{st.session_state.user_email}**")
    st.sidebar.caption(f"Role: {'👑 Admin' if is_admin else '👤 Member'}")

    if st.sidebar.button("🚪 Logout"):
        for key in ["logged_in", "user_email", "user_role"]:
            st.session_state[key] = "" if key != "logged_in" else False
        st.rerun()

    nav_options = ["🔮 Prediction", "📊 Analytics", "📤 CSV Upload"]
    if is_admin:
        nav_options.append("👑 Admin Panel")
    page = st.sidebar.radio("Navigate", nav_options)

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 1: PREDICTION
    # ═══════════════════════════════════════════════════════════════════
    if page == "🔮 Prediction":
        st.title("🔮 Customer Segment Prediction")
        st.markdown("Enter customer details to predict their segment.")

        col1, col2, col3 = st.columns(3)
        with col1:
            customer_id = st.number_input(
                "Customer ID (optional — auto-assigned if 0)",
                min_value=0, value=0, step=1,
                help="Unique customer identifier. Leave as 0 to auto-assign.",
            )
        with col2:
            income = st.number_input(
                "Annual Income (k$)",
                min_value=1.0, max_value=200.0, value=50.0, step=1.0, format="%.1f",
                help="Customer's annual income in thousands of dollars.",
            )
        with col3:
            spending = st.number_input(
                "Spending Score (1-100)",
                min_value=1.0, max_value=100.0, value=50.0, step=1.0, format="%.1f",
                help="Customer's spending score between 1 and 100.",
            )

        if st.button("🚀  Predict Segment", use_container_width=True):
            with st.spinner("Calling prediction API..."):
                try:
                    payload = {"income": income, "spending": spending}
                    if customer_id > 0:
                        payload["customer_id"] = customer_id
                    resp = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(
                                f'<div class="metric-card"><p>Predicted Cluster</p>'
                                f'<h2>Cluster {data["cluster"]}</h2></div>',
                                unsafe_allow_html=True,
                            )
                        with c2:
                            st.markdown(
                                f'<div class="metric-card"><p>Segment Label</p>'
                                f'<h2>{data["label"]}</h2></div>',
                                unsafe_allow_html=True,
                            )
                        st.markdown(
                            f'<div class="insight-box">💡 <strong>Business Insight:</strong> '
                            f'{data["insight"]}</div>',
                            unsafe_allow_html=True,
                        )
                        st.success(f"Record saved — Customer ID: {data['customer_id']}")
                    elif resp.status_code == 422:
                        st.error("Validation error — check that income > 0 and spending is between 1-100.")
                    else:
                        st.error(f"API error {resp.status_code}: {resp.text}")
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ Cannot connect to backend.")

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 2: ANALYTICS (Enterprise Dashboard)
    # ═══════════════════════════════════════════════════════════════════
    elif page == "📊 Analytics":
        st.title("📊 Enterprise Analytics Dashboard")

        try:
            resp = requests.get(f"{API_URL}/analytics/detailed", timeout=10)
            if resp.status_code != 200:
                st.error("Failed to fetch analytics.")
                return

            data = resp.json()
            dist = data["distribution"]
            stats = data["cluster_stats"]
            customers = data["customers"]

            if not dist:
                st.info("No data yet. Make predictions or upload a CSV first!")
                return

            df_cust = pd.DataFrame(customers)
            df_dist = pd.DataFrame(dist)
            df_stats = pd.DataFrame(stats)

            # --- Cluster legend ---
            render_cluster_legend()

            # --- Summary metrics row ---
            total = sum(d["count"] for d in dist)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Customers", total)
            m2.metric("Active Segments", len(dist))
            m3.metric("Avg Income", f"{df_cust['income'].mean():.1f}k$")
            m4.metric("Avg Spending", f"{df_cust['spending'].mean():.1f}")

            st.markdown("---")

            # ============================================================
            # ROW 1: Bar chart + Pie chart
            # ============================================================
            st.subheader("1️⃣ Cluster Distribution")
            r1c1, r1c2 = st.columns(2)

            with r1c1:
                df_dist["label"] = df_dist["cluster"].map(CLUSTER_LABELS)
                fig, ax = plt.subplots(figsize=(8, 5))
                colors = [CLUSTER_COLORS.get(c, "#999") for c in df_dist["cluster"]]
                bars = ax.bar(df_dist["label"], df_dist["count"], color=colors, edgecolor="white", linewidth=1.2)
                for bar, count in zip(bars, df_dist["count"]):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                            str(count), ha="center", va="bottom", fontweight="bold", fontsize=11)
                ax.set_ylabel("Count", fontsize=11)
                ax.set_title("Customers per Segment", fontsize=13, fontweight="bold")
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
                plt.xticks(rotation=25, ha="right", fontsize=9)
                plt.tight_layout()
                st.pyplot(fig)

            with r1c2:
                fig2, ax2 = plt.subplots(figsize=(7, 5))
                labels = [CLUSTER_LABELS.get(d["cluster"], f"C{d['cluster']}") for d in dist]
                sizes = [d["count"] for d in dist]
                pie_colors = [CLUSTER_COLORS.get(d["cluster"], "#999") for d in dist]
                wedges, texts, autotexts = ax2.pie(
                    sizes, labels=labels, colors=pie_colors, autopct="%1.1f%%",
                    startangle=140, pctdistance=0.8, textprops={"fontsize": 9},
                )
                for at in autotexts:
                    at.set_fontweight("bold")
                centre_circle = plt.Circle((0, 0), 0.55, fc="white")
                ax2.add_artist(centre_circle)
                ax2.set_title("Segment Share (%)", fontsize=13, fontweight="bold")
                plt.tight_layout()
                st.pyplot(fig2)

            st.markdown("---")

            # ============================================================
            # ROW 2: Scatter plot (Income vs Spending)
            # ============================================================
            st.subheader("2️⃣ Income vs Spending — Cluster Scatter Plot")
            fig3, ax3 = plt.subplots(figsize=(10, 6))
            for cid in sorted(df_cust["cluster"].unique()):
                subset = df_cust[df_cust["cluster"] == cid]
                ax3.scatter(
                    subset["income"], subset["spending"],
                    c=CLUSTER_COLORS.get(cid, "#999"),
                    label=CLUSTER_LABELS.get(cid, f"Cluster {cid}"),
                    s=60, alpha=0.75, edgecolors="white", linewidth=0.5,
                )
            ax3.set_xlabel("Annual Income (k$)", fontsize=12)
            ax3.set_ylabel("Spending Score", fontsize=12)
            ax3.set_title("Customer Clusters", fontsize=14, fontweight="bold")
            ax3.legend(fontsize=9, loc="upper left", framealpha=0.9)
            ax3.spines["top"].set_visible(False)
            ax3.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig3)

            st.markdown("---")

            # ============================================================
            # ROW 3: Box plots (Income & Spending per cluster)
            # ============================================================
            st.subheader("3️⃣ Distribution per Cluster — Box Plots")
            r3c1, r3c2 = st.columns(2)

            palette = [CLUSTER_COLORS.get(i, "#999") for i in sorted(df_cust["cluster"].unique())]

            with r3c1:
                fig4, ax4 = plt.subplots(figsize=(8, 5))
                sns.boxplot(
                    data=df_cust, x="cluster", y="income",
                    palette=palette, ax=ax4, width=0.5,
                )
                ax4.set_xlabel("Cluster", fontsize=11)
                ax4.set_ylabel("Annual Income (k$)", fontsize=11)
                ax4.set_title("Income Distribution by Cluster", fontsize=13, fontweight="bold")
                ax4.spines["top"].set_visible(False)
                ax4.spines["right"].set_visible(False)
                plt.tight_layout()
                st.pyplot(fig4)

            with r3c2:
                fig5, ax5 = plt.subplots(figsize=(8, 5))
                sns.boxplot(
                    data=df_cust, x="cluster", y="spending",
                    palette=palette, ax=ax5, width=0.5,
                )
                ax5.set_xlabel("Cluster", fontsize=11)
                ax5.set_ylabel("Spending Score", fontsize=11)
                ax5.set_title("Spending Distribution by Cluster", fontsize=13, fontweight="bold")
                ax5.spines["top"].set_visible(False)
                ax5.spines["right"].set_visible(False)
                plt.tight_layout()
                st.pyplot(fig5)

            st.markdown("---")

            # ============================================================
            # ROW 4: Correlation Heatmap
            # ============================================================
            st.subheader("4️⃣ Correlation Heatmap")
            corr_df = df_cust[["income", "spending", "cluster"]].rename(columns={
                "income": "Income", "spending": "Spending", "cluster": "Cluster"
            })
            fig6, ax6 = plt.subplots(figsize=(6, 5))
            sns.heatmap(
                corr_df.corr(), annot=True, cmap="coolwarm", fmt=".2f",
                linewidths=1, ax=ax6, vmin=-1, vmax=1, square=True,
            )
            ax6.set_title("Feature Correlation Matrix", fontsize=13, fontweight="bold")
            plt.tight_layout()
            st.pyplot(fig6)

            st.markdown("---")

            # ============================================================
            # ROW 5: Per-cluster summary statistics table
            # ============================================================
            st.subheader("5️⃣ Cluster Summary Statistics")
            df_stats_display = df_stats.copy()
            df_stats_display["segment"] = df_stats_display["cluster"].map(CLUSTER_LABELS)
            df_stats_display = df_stats_display[[
                "cluster", "segment", "count",
                "avg_income", "min_income", "max_income",
                "avg_spending", "min_spending", "max_spending",
            ]]
            df_stats_display.columns = [
                "Cluster", "Segment", "Count",
                "Avg Income", "Min Income", "Max Income",
                "Avg Spending", "Min Spending", "Max Spending",
            ]
            st.dataframe(df_stats_display, use_container_width=True, hide_index=True)

            st.markdown("---")

            # ============================================================
            # ROW 6: Full customer table + CSV export
            # ============================================================
            st.subheader("6️⃣ Customer Records")
            df_display = df_cust.copy()
            df_display["segment"] = df_display["cluster"].map(CLUSTER_LABELS)
            st.dataframe(
                df_display[["customer_id", "income", "spending", "cluster", "segment", "created_at", "updated_at"]],
                use_container_width=True, hide_index=True,
            )

            # CSV export
            csv_data = df_display[["customer_id", "income", "spending", "cluster", "segment"]].to_csv(index=False)
            st.download_button(
                label="⬇️  Export Customers as CSV",
                data=csv_data,
                file_name="customer_segments.csv",
                mime="text/csv",
                use_container_width=True,
            )

        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend. Is the API server running?")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 3: CSV UPLOAD
    # ═══════════════════════════════════════════════════════════════════
    elif page == "📤 CSV Upload":
        st.title("📤 Bulk Customer Import")
        st.markdown(
            "Upload a **headerless CSV** with 3 columns:\n"
            "1. **Customer ID** (unique integer)\n"
            "2. **Annual Income** (k$)\n"
            "3. **Spending Score** (1-100)\n\n"
            "Existing customers with the same ID will be **updated** (not duplicated)."
        )

        st.info("💡 The CSV must NOT contain column headers — just raw data rows.")

        uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

        if uploaded is not None:
            content = uploaded.read().decode("utf-8")
            uploaded.seek(0)

            # Preview
            lines = [l for l in content.strip().split("\n") if l.strip()]
            st.markdown(f"**Preview** — {len(lines)} rows detected")
            preview_data = []
            for line in lines[:10]:
                parts = line.split(",")
                if len(parts) >= 3:
                    preview_data.append({
                        "Customer ID": parts[0].strip(),
                        "Income": parts[1].strip(),
                        "Spending": parts[2].strip(),
                    })
            if preview_data:
                st.dataframe(pd.DataFrame(preview_data), hide_index=True)
            if len(lines) > 10:
                st.caption(f"...and {len(lines) - 10} more rows")

            if st.button("🚀 Upload & Process", use_container_width=True):
                with st.spinner("Uploading and processing..."):
                    try:
                        uploaded.seek(0)
                        files = {"file": (uploaded.name, uploaded, "text/csv")}
                        resp = requests.post(f"{API_URL}/upload-csv", files=files, timeout=60)
                        if resp.status_code == 200:
                            summary = resp.json()
                            st.success(
                                f"✅ Upload complete — "
                                f"**{summary['inserted']}** inserted, "
                                f"**{summary['updated']}** updated"
                            )
                            if summary.get("errors"):
                                st.warning(f"⚠️ {len(summary['errors'])} row(s) had errors:")
                                st.json(summary["errors"][:20])
                        else:
                            st.error(f"Upload failed ({resp.status_code}): {resp.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Cannot connect to backend.")

    # ═══════════════════════════════════════════════════════════════════
    # PAGE 4: ADMIN PANEL (admin only)
    # ═══════════════════════════════════════════════════════════════════
    elif page == "👑 Admin Panel":
        st.title("👑 Admin Panel — User Management")

        admin_headers = {"X-User-Role": "admin"}

        # --- Section: Current Users ---
        st.subheader("📋 Registered Users")
        try:
            resp = requests.get(f"{API_URL}/admin/users", headers=admin_headers, timeout=10)
            if resp.status_code == 200:
                users = resp.json()
                df_users = pd.DataFrame(users)
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.error("Failed to load users.")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Cannot connect to backend.")

        st.markdown("---")

        # --- Section: Create New User ---
        st.subheader("➕ Create New User")
        with st.form("create_user_form"):
            new_email = st.text_input("Email", placeholder="newuser@mgit.ac.in")
            new_password = st.text_input("Password", type="password", value="12345678")
            new_role = st.selectbox("Role", ["member", "admin"])
            create_submitted = st.form_submit_button("Create User", use_container_width=True)

            if create_submitted:
                if not new_email:
                    st.error("Email is required.")
                elif not new_password:
                    st.error("Password is required.")
                else:
                    try:
                        resp = requests.post(
                            f"{API_URL}/admin/users",
                            json={"email": new_email.strip(), "password": new_password, "role": new_role},
                            headers=admin_headers,
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.success(f"✅ User '{new_email}' created successfully!")
                            st.rerun()
                        elif resp.status_code == 409:
                            st.error(f"User '{new_email}' already exists.")
                        else:
                            st.error(f"Error: {resp.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Cannot connect to backend.")

        st.markdown("---")

        # --- Section: Change Password ---
        st.subheader("🔑 Change User Password")
        with st.form("change_password_form"):
            target_email = st.text_input("User Email", placeholder="user@mgit.ac.in")
            new_pwd = st.text_input("New Password", type="password")
            pwd_submitted = st.form_submit_button("Update Password", use_container_width=True)

            if pwd_submitted:
                if not target_email or not new_pwd:
                    st.error("Both email and new password are required.")
                else:
                    try:
                        resp = requests.put(
                            f"{API_URL}/admin/users/password",
                            json={"email": target_email.strip(), "new_password": new_pwd},
                            headers=admin_headers,
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.success(f"✅ Password updated for '{target_email}'.")
                        elif resp.status_code == 404:
                            st.error(f"User '{target_email}' not found.")
                        else:
                            st.error(f"Error: {resp.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Cannot connect to backend.")

        st.markdown("---")

        # --- Section: Delete User ---
        st.subheader("🗑️ Delete User")
        with st.form("delete_user_form"):
            del_email = st.text_input("Email to delete", placeholder="user@mgit.ac.in")
            del_submitted = st.form_submit_button("Delete User", use_container_width=True)

            if del_submitted:
                if not del_email:
                    st.error("Email is required.")
                elif del_email.strip() == st.session_state.user_email:
                    st.error("❌ You cannot delete your own account.")
                else:
                    try:
                        resp = requests.delete(
                            f"{API_URL}/admin/users/{del_email.strip()}",
                            headers=admin_headers,
                            timeout=10,
                        )
                        if resp.status_code == 200:
                            st.success(f"✅ User '{del_email}' deleted.")
                            st.rerun()
                        elif resp.status_code == 404:
                            st.error(f"User '{del_email}' not found.")
                        else:
                            st.error(f"Error: {resp.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("⚠️ Cannot connect to backend.")


# ═══════════════════════════════════════════════════════════════════════════
# ROUTING — login gate
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.logged_in:
    show_app()
else:
    show_login()
