using ExtensionMethodDemo;
internal static class Contracts
{
static void Check(bool condition,string message){if(!condition)throw new Exception(message);}
static void Throws<T>(Action action) where T:Exception{try{action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
static async Task ThrowsAsync<T>(Func<Task> action) where T:Exception{try{await action();}catch(T){return;}throw new Exception("Expected "+typeof(T).Name);}
public static void Main(){
var input=new List<OrderLine>{new("A",2,5m)};var order=new Order("A",input);input.Clear();Check(order.Total()==10m,"defensive list copy");var source=new List<Order>{order};var result=source.WithMinimumTotal(10m);Check(result.Count==1&&ReferenceEquals(result[0],order),"result references");result.Clear();Check(source.Count==1,"container independent");Throws<ArgumentNullException>(()=>OrderExtensions.Total(null!));Throws<ArgumentOutOfRangeException>(()=>source.WithMinimumTotal(-1));
}
}
