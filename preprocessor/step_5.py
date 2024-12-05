import sqlite3

db = "output/meta.sqlite"

def main():
    print("Step #5 - Count total stars for each cluster")

    conn = sqlite3.connect(db)
    cursor = conn.cursor();

    cursor.execute(
       "SELECT cluster, SUM(stars) as total_stars FROM repositories GROUP BY cluster"
    )
    cluster_star_count = dict(cursor.fetchall())

    cursor.execute("ALTER TABLE clusters ADD COLUMN stars INTEGER")
    conn.commit()

    try:
        for cluster_id, total_stars in cluster_star_count.items():
            cursor.execute("UPDATE clusters SET stars = ? WHERE id = ?", (total_stars, cluster_id))
        conn.commit()
        print("Done!")
    except sqlite3.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
