using AsyncCheckoutDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static async Task Main(){
var source=new ControlledPriceSource();var s=new CheckoutService(source);var task=s.CalculateAsync("A","B");Check(!task.IsCompleted,"no suspension");source.Complete("B",2);Check(!task.IsCompleted,"completed with one price");source.Complete("A",3);var value=await task.WaitAsync(TimeSpan.FromSeconds(5));Check(value.Subtotal==5&&value.Total==5.5m,"WhenAll result");
await ThrowsAsync<ArgumentException>(()=>s.CalculateAsync("", "B"));Throws<InvalidOperationException>(()=>source.Complete("A",1));
}
}
