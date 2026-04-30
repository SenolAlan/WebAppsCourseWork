'''import sqlite3
from DynamicWebsite import app, db, User, VinylsDb

OLD_DB = "instance/vinyls.db"   # old database
NEW_OWNER = "imported"


with app.app_context():
    db.create_all()

    conn = sqlite3.connect(OLD_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Old DB tables:", [table[0] for table in cursor.fetchall()])

    cursor.execute("SELECT * FROM VinylsDb")
    rows = cursor.fetchall()

    for row in rows:
        vinyl = VinylsDb(
            vinyl_artist=row["vinyl_artist"],
            vinyl_name=row["vinyl_name"],
            vinyl_genre=row["vinyl_genre"],
            vinyl_year=row["vinyl_year"],
            vinyl_image=row["vinyl_image"],
            vinyl_price=row["vinyl_price"],
            vinyl_impact=row["vinyl_impact"],
        )

        db.session.add(vinyl)

    db.session.commit()
    conn.close()

    print(f"Imported {len(rows)} vinyls into app.db")'''