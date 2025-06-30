db = connect('mongodb://localhost:27017/?maxPoolSize=20&w=majority');
const databases = db.adminCommand({ listDatabases: 1 }).databases;
databases.forEach(function (database) {
    const dbName = database.name;
    if (dbName !== 'admin' && dbName !== 'config' && dbName !== 'local') {
        print(`Dropping database: ${dbName}`);
        db.getSiblingDB(dbName).dropDatabase();
    }
});

print("All non-system dbs have been deleted")