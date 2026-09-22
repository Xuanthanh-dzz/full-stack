using ResourceLifetimeDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static async Task Main(){
var path="contract-audit.log";var owner=new AuditFile(path);try{using(owner){owner.WriteLine("saved");throw new InvalidOperationException();}}catch(InvalidOperationException){}Check(File.ReadAllText(path)=="saved"+Environment.NewLine,"cleanup flushed");owner.Dispose();Throws<ObjectDisposedException>(()=>owner.WriteLine("late"));using(var exclusive=new FileStream(path,FileMode.Open,FileAccess.ReadWrite,FileShare.None)){}File.Delete(path);
var session=new AsyncSession();await session.DisposeAsync();await session.DisposeAsync();await ThrowsAsync<ObjectDisposedException>(()=>session.SendAsync("late"));
}
}
