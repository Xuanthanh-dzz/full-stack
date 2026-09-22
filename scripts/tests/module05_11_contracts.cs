using ThreadSafetyDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static async Task Main(){
var unsafeCounter=new CoordinatedUnsafeCounter();var a=unsafeCounter.IncrementAsync();var b=unsafeCounter.IncrementAsync();await unsafeCounter.BothReadersReady.WaitAsync(TimeSpan.FromSeconds(5));unsafeCounter.ReleaseWrites();await Task.WhenAll(a,b);Check(unsafeCounter.Value==1,"deterministic lost update");var locked=new LockedCounter();var atomic=new AtomicCounter();Parallel.For(0,1000,_=>{locked.Increment();atomic.Increment();});Check(locked.Value==1000&&atomic.Value==1000,"counter protocol");
}
}
